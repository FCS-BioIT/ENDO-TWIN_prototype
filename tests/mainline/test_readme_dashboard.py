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
            f"**{lit['seed_search_candidates']}** candidate records",
            f"**{lit['bundle_screen_2026_10_21_papers']}** papers screened",
            f"tiers A {tiers['A']} / B {tiers['B']} / C {tiers['C']}",
            f"stated **{lit['reaudit_2026_09_28_stated_corpus_pdfs']}**-PDF corpus",
            f"**{lit['reaudit_2026_09_28_enumerated_active_pack']}** papers enumerated",
            f"**{lit['registered_references']}** registered references",
            f"all **{lit['registered_crossref_resolved']}** resolved against Crossref",
            f"**{lit['pdf_manifest_full_text_inspected']}** papers full-text inspected",
        ):
            self.assertQuoted(phrase)

    def test_evidence(self):
        ev = METRICS["evidence"]
        actions = ev["citation_adjudications_by_action"]
        for phrase in (
            f"**{ev['experimental_evidence_rows']}** edge-level evidence rows",
            (
                f"**{ev['active_rows']}** active rows on **{ev['active_edges_with_rows']}** edges "
                f"citing **{ev['active_unique_references']}** papers"
            ),
            (
                f"**{ev['full_text_graded_rows']}** rows graded from full text on "
                f"**{ev['full_text_graded_edges']}** edges"
            ),
            (
                f"**{ev['v060_declared_edges_with_primary_reference']}** of "
                f"**{ev['v060_declared_edges']}** declared v0.6.0 edges"
            ),
            f"**{ev['citation_adjudications']}** citation adjudications",
            f"(**{actions['retract']}** retractions, **{actions['attach']}** attachments)",
        ):
            self.assertQuoted(phrase)

    def test_network_and_modelling(self):
        v060 = METRICS["network_versions"]["adoc-literature-superset-v0.6.0"]
        alt = METRICS["alternatives_and_adjudication"]
        for phrase in (
            (
                f"**{v060['nodes']}** nodes, **{v060['dependencies']}** dependencies "
                f"(**{v060['activations']}** activating, **{v060['inhibitions']}** inhibitory)"
            ),
            (
                f"**{v060['distinct_boolean_functions']}** distinct Boolean functions in "
                f"**{v060['alias_classes']}** alias classes"
            ),
            f"**{v060['absorbed_or_never_binding']}** of {v060['dependencies']} dependencies absorbed",
            f"**{v060['phenotype_inert_nodes']}** phenotype-inert nodes",
            f"**{len(METRICS['network_versions'])}** model versions",
            f"**{alt['gate3_candidate_rule_variants']}** Gate 3a candidate rule variants",
            f"a **{alt['u6b_muc1_family_members']}**-member rule family",
            f"**{alt['candidate_node_dispositions']}** candidate nodes adjudicated",
            f"**{alt['rules_changed_after_literature_reaudit']}** executable rules changed",
        ):
            self.assertQuoted(phrase)

    def test_experimental_data(self):
        x = METRICS["experimental_data"]
        for phrase in (
            f"**{x['secreted_protein_rows']}** rows, **{x['secreted_protein_observed_values']}** observed values",
            (
                f"**{n(x['scrna_cells'])}** cells, **{x['scrna_donors']}** donors, "
                f"**{x['scrna_samples']}** samples, **{n(x['scrna_epithelial_cells'])}** epithelial and "
                f"**{n(x['scrna_stromal_cells'])}** stromal cells, **{x['scrna_cell_state_labels']}** cell-state labels"
            ),
        ):
            self.assertQuoted(phrase)

    def test_embryo_adhesion_is_not_presented_as_endotwin_evidence(self):
        # prototype-only endpoint; scope decision in docs/experimental_data.md, section 3.
        self.assertNotRegex(DASHBOARD.lower(), r"adhesion|embryo")

    def test_analyses_sensitivity_and_mainline(self):
        self.assertQuoted(
            f"**{len(METRICS['completed_analyses'])}** completed prototype analyses"
        )
        rates = json.loads((RESULTS / "rate_sensitivity_summary.json").read_text())
        self.assertQuoted(
            f"**{rates['records_converged']}** of **{rates['records']}** steady-state predictions "
            f"unchanged under **{rates['samples']}** random rate sets"
        )
        main = METRICS["endotwin_mainline"]
        structure = main["structure"]
        families = main["rule_variant_families"]
        self.assertQuoted(
            f"**{structure['nodes']}** nodes, **{structure['dependencies']}** dependencies, "
            f"**{structure['distinct_functions']}** distinct Boolean functions"
        )
        self.assertQuoted(
            f"**{len(families)}** competing-hypothesis families, "
            f"**{sum(len(v) for v in families.values())}** rule variants, "
            f"**{main['rule_variant_scenarios']}** executable scenarios"
        )
        self.assertQuoted(
            f"**{main['protocol_conditions']}** protocol conditions, "
            f"**{main['matched_comparisons']}** matched comparisons"
        )
        confirm = json.loads((RESULTS / "maboss_confirmation_summary.json").read_text())
        self.assertEqual(confirm["unconverged_phases"], 0)
        self.assertQuoted(f"all **{confirm['records']}** simulated phases converge")

    def test_software_verification(self):
        records = json.loads(SUITE_RECORDS.read_text())
        run = records["endotwin_full_suite"]
        self.assertQuoted(
            f"**{n(run['ran'])}** automated tests in this repository (**{n(run['passed'])}** passed, "
            f"**{run['failed']}** failed, **{run['skipped']}** skipped)"
        )
        base = records["source_baseline"]
        self.assertQuoted(f"**{n(base['ran'])}** at the prototype source commit")
        self.assertQuoted(
            f"**{n(records['historical_benchmark']['ran'])}** on the 2026-10-16 benchmark"
        )


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
