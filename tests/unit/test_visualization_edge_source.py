"""The figure must draw what the model computes, not what has been cited.

`build_edge_views` used to read `edge_evidence.tsv`, a record of what has been
*cited*. That is not the set the model *computes*, and the two are not even
nested: for the superset the network computes 96 non-self dependencies against 93
evidence rows, so the animation drew the retired `LE081` relation the model does
not compute and omitted four real dependencies.

These tests pin the direction of authority: topology comes from `network.bnd`,
evidence is joined in only for styling.
"""

from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.model.runtime import available_models, resolve_model
from dt_adoc.model.topology import (
    CATEGORY_TO_STATUS,
    derive_dependencies,
    load_adjudications,
    parse_bnd_rules,
)
from dt_adoc.reporting.dynamics import VIEW_FULL, build_network_view

SUPERSET = "adoc-literature-superset-v0.3.0"


def evidence_pairs(model_version: str) -> set[tuple[str, str]]:
    spec = resolve_model(model_version, ROOT)
    with spec.edge_evidence.open(encoding="utf-8", newline="") as handle:
        return {
            (row["source"], row["target"])
            for row in csv.DictReader(handle, delimiter="\t")
        }


class EdgeSourceIsTheNetworkTest(unittest.TestCase):
    def test_every_executable_dependency_is_drawn(self) -> None:
        """The full view must represent every non-self dependency the model
        computes, for every registered model."""
        for model_version in available_models(ROOT):
            with self.subTest(model=model_version):
                spec = resolve_model(model_version, ROOT)
                expected = set(derive_dependencies(parse_bnd_rules(spec.network_bnd)))
                view = build_network_view(
                    model_version=model_version, view=VIEW_FULL, root=ROOT
                )
                drawn = {(edge.source, edge.target) for edge in view.edges}
                self.assertEqual(sorted(expected - drawn), [], model_version)

    def test_no_drawn_edge_is_absent_from_the_network(self) -> None:
        """A drawn edge the model does not compute is a fabricated claim."""
        for model_version in available_models(ROOT):
            with self.subTest(model=model_version):
                spec = resolve_model(model_version, ROOT)
                computed = set(derive_dependencies(parse_bnd_rules(spec.network_bnd)))
                view = build_network_view(
                    model_version=model_version, view=VIEW_FULL, root=ROOT
                )
                drawn = {(edge.source, edge.target) for edge in view.edges}
                self.assertEqual(sorted(drawn - computed), [], model_version)

    def test_the_retired_relation_is_not_drawn(self) -> None:
        """LE081 is a curated row for a relation the superset does not compute.

        It is retained in edge_evidence.tsv with its 8 assertions as history and
        marked `retired` in topology.tsv. It must never reach the figure.
        """
        view = build_network_view(model_version=SUPERSET, view=VIEW_FULL, root=ROOT)
        drawn = {(edge.source, edge.target) for edge in view.edges}
        self.assertIn(
            ("E_RECEPTIVE_SURFACE", "OUT_MATERNAL_ADHESION_COMPETENCE"),
            evidence_pairs(SUPERSET),
            "precondition: LE081 is still in the evidence table",
        )
        self.assertNotIn(
            ("E_RECEPTIVE_SURFACE", "OUT_MATERNAL_ADHESION_COMPETENCE"), drawn
        )

    def test_evidence_availability_does_not_define_topology(self) -> None:
        """An executing dependency with no evidence row is still drawn.

        The superset has four: three adjudicated `unprovenanced` and one
        `logical_aggregate`, all recorded in
        config/topology_parity_exemptions.tsv. Dropping them would let the
        citation backlog silently reshape the network, which is the defect this
        module exists to prevent. The expected set is read from the adjudication
        registry rather than hard-coded, so curating one updates both at once.
        """
        view = build_network_view(model_version=SUPERSET, view=VIEW_FULL, root=ROOT)
        drawn = {(edge.source, edge.target) for edge in view.edges}
        uncited = drawn - evidence_pairs(SUPERSET)
        adjudicated = load_adjudications(ROOT / "config/topology_parity_exemptions.tsv")
        expected = {
            pair
            for pair, row in adjudicated.items()
            if CATEGORY_TO_STATUS[row["category"]] != "retired"
        }
        self.assertEqual(uncited, expected, sorted(uncited ^ expected))
        for edge in view.edges:
            if (edge.source, edge.target) in uncited:
                self.assertEqual(edge.confidence, "", edge.source)

    def test_edge_count_matches_the_dependency_count_not_the_row_count(self) -> None:
        """The distinction that was previously invisible."""
        spec = resolve_model(SUPERSET, ROOT)
        view = build_network_view(model_version=SUPERSET, view=VIEW_FULL, root=ROOT)
        self.assertEqual(
            len(view.edges),
            len(derive_dependencies(parse_bnd_rules(spec.network_bnd))),
        )
        self.assertNotEqual(len(view.edges), len(evidence_pairs(SUPERSET)))


class DerivedPolarityTest(unittest.TestCase):
    def test_signs_come_from_the_rules_and_match_curation(self) -> None:
        """Polarity is parsed from the rule, and agrees with every curated sign.

        A token-local heuristic would mis-sign X_MECHANICAL_PERMISSIVE_ECM,
        which negates a parenthesised group.
        """
        for model_version in available_models(ROOT):
            with self.subTest(model=model_version):
                spec = resolve_model(model_version, ROOT)
                with spec.edge_evidence.open(encoding="utf-8", newline="") as handle:
                    curated = {
                        (row["source"], row["target"]): row["sign"]
                        for row in csv.DictReader(handle, delimiter="\t")
                    }
                view = build_network_view(
                    model_version=model_version, view=VIEW_FULL, root=ROOT
                )
                for edge in view.edges:
                    expected = curated.get((edge.source, edge.target))
                    if expected is not None:
                        self.assertEqual(
                            edge.sign, expected, f"{edge.source}->{edge.target}"
                        )

    def test_the_parenthesised_negation_is_signed_as_inhibition(self) -> None:
        view = build_network_view(model_version=SUPERSET, view=VIEW_FULL, root=ROOT)
        signs = {
            (e.source, e.target): e.sign
            for e in view.edges
            if e.target == "X_MECHANICAL_PERMISSIVE_ECM"
        }
        for source in (
            "IN_ER_STRESS_EXCESS",
            "IN_HIGH_ECM_STIFFNESS",
            "X_MECHANICAL_STRESS_RELAY",
        ):
            self.assertEqual(
                signs[(source, "X_MECHANICAL_PERMISSIVE_ECM")], "inhibition"
            )


if __name__ == "__main__":
    unittest.main()
