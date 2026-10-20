"""What the README's front page must say, and which numbers it may quote.

Replaces ``test_superset_animation.ReadmePrimaryFigureTest``, which pinned the
2026-07-29 layout (v0.4 pathway animation as the primary figure). On
2026-09-23 the owner asked for the README to describe the current state and to
demote figures that no longer do, so the primary figures are now the network
overview and the functional-endpoint figure, both regenerated from the
v0.5 scaffold with provenance proving it executable-identical to v0.4, plus the
v0.4 pathway animation re-embedded (owner request) as exploratory, qualitative
dynamics. On 2026-10-07 that animation was re-rendered from the current
markerless v0.6.0; the v0.4 render is kept as a reproducibility artifact. The
same day the network overview was re-rendered from v0.6.0 and the v0.5.0 render
demoted. The functional-endpoint figure stays a v0.5.0 render: its pipeline is
pinned to v0.5.0 and reads treatment from marker inputs. The demoted figures stay
in the repository and stay linked.

The README's structural summary has two parts. The current one (v0.6.0) is
checked against ``docs/intervention_layer_stage3/structure_counts.json`` and the
v0.6.0 network sidecar; the historical one (U5, v0.5.0) against the U5 audit JSON.
No number is typed into this test, so a later model change fails here instead of
leaving the front page stale, and the current part may not quote the U5 numbers.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = (ROOT / "README.md").read_text(encoding="utf-8")
AUDIT = json.loads(
    (ROOT / "docs/u5_structural_audit/u5_audit_summary.json").read_text(
        encoding="utf-8"
    )
)
CURRENT_VERSION = "adoc-literature-superset-v0.6.0"
STRUCTURE = json.loads(
    (ROOT / "docs/intervention_layer_stage3/structure_counts.json").read_text(
        encoding="utf-8"
    )
)
CURRENT = STRUCTURE["versions"][CURRENT_VERSION]
NETWORK_SIDECAR = json.loads(
    (ROOT / "docs/assets/adoc_network_overview_v0.6.0_metadata.json").read_text(
        encoding="utf-8"
    )
)
CURRENT_HEADING = "**Current structure (`v0.6.0`)**"
HISTORICAL_HEADING = "**Pinned historical results: the U5 audit of `v0.5.0`**"

PRIMARY = (
    # Re-rendered 2026-10-07 from v0.6.0; the v0.5.0 render is demoted.
    "docs/assets/adoc_network_overview_v0.6.0.png",
    # Historical v0.5.0 render, labelled as such: no v0.6.0 pathway exists.
    "docs/assets/adoc_functional_endpoint_v0.5.0.png",
    # Re-embedded 2026-09-23 at the owner's request as EXPLORATORY dynamics;
    # re-rendered 2026-10-07 from v0.6.0, the current executable increment.
    "docs/assets/adoc_superset_pathway_dynamics_v0.6.0.gif",
)
DEMOTED = (
    "docs/assets/adoc_network_overview_v0.5.0.png",
    "docs/assets/adoc_concordance_v0.4.0.png",
    "docs/assets/adoc_superset_structure_v0.4.0.png",
    "docs/assets/adoc_maboss_pathway_dynamics.gif",
    "docs/assets/adoc_superset_pathway_dynamics_v0.4.0.gif",
)


def _embedded(text: str) -> set[str]:
    return set(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text))


def _flat(text: str) -> str:
    """Collapse line breaks and indentation, so wrapping cannot hide a number."""
    return " ".join(text.split())


def _structure_parts() -> tuple[str, str]:
    section = README[README.index("## What the model cannot distinguish") :]
    section = section[: section.index("## What the transcriptome adds")]
    current = section[
        section.index(CURRENT_HEADING) : section.index(HISTORICAL_HEADING)
    ]
    historical = section[section.index(HISTORICAL_HEADING) :]
    return _flat(current), _flat(historical)


class ReadmeContractTest(unittest.TestCase):
    def test_primary_figures_are_embedded_and_exist(self) -> None:
        self.assertEqual(_embedded(README), set(PRIMARY))
        for path in PRIMARY:
            self.assertTrue((ROOT / path).is_file(), path)

    def test_demoted_figures_are_linked_not_embedded(self) -> None:
        secondary = README[README.index("### Secondary and historical figures") :]
        for path in DEMOTED:
            self.assertIn(path, secondary, path)
            self.assertTrue((ROOT / path).is_file(), path)

    def test_the_animation_is_captioned_as_exploratory_and_qualitative(self) -> None:
        caption = README[README.index("## Exploratory dynamics") :]
        caption = caption[: caption.index("## What the model cannot distinguish")]
        for token in (
            "**Exploratory dynamics.**",
            "dimensionless",
            "not mapped to experimental days",
            "qualitatively, not as calibrated temporal predictions",
            "not a temporal prediction",
            "adoc-literature-superset-v0.6.0",
            "config/protocols_markerless.yaml",
            "adoc_superset_pathway_dynamics_v0.6.0_metadata.json",
        ):
            self.assertIn(token, caption, token)
        self.assertNotIn("adoc_superset_pathway_dynamics_v0.4.0", caption)

    def test_the_model_lineage_is_stated_precisely(self) -> None:
        self.assertIn(
            "`adoc-literature-superset-v0.4.0` is the immutable executable parent",
            README,
        )
        self.assertIn("**scaffold**", README)
        self.assertIn("**byte-identical to v0.4.0**", README)
        self.assertIn("It is not a new biological model.", README)
        self.assertTrue(AUDIT["file_identity"]["executable_byte_identical"])

    def test_the_load_bearing_caveats_are_present(self) -> None:
        for token in (
            "not comparable",
            "disjoint between replicate\n> indices",
            "not an i.i.d. Monte Carlo SE",
            "not MaBoSS's node error column",
            "Wilson 95% CI on the per-embryo proportion",
            "only the ordering",
            "not a fit",
            "dimensionless",
            "matched-unit",
            "not** an independent biological replicate",
            "**None.**",
            "prospective discriminating experiment",
        ):
            self.assertIn(token, README, token)

    def test_current_structural_summary_matches_the_v060_counts(self) -> None:
        current, _historical = _structure_parts()
        n = CURRENT["free_variables"]
        self.assertIn(
            f"all 2^{n} = {CURRENT['enumerated_assignments']:,} free-variable assignments",
            current,
        )
        self.assertEqual(2**n, CURRENT["enumerated_assignments"])
        self.assertIn(
            f"**{CURRENT['nodes']} named nodes implement "
            f"{CURRENT['distinct_composed_functions']} distinct Boolean functions**, "
            f"in {CURRENT['alias_class_count']} alias classes",
            current,
        )
        self.assertIn(
            f"The {n} free variables are the {CURRENT['input_nodes']} input nodes "
            f"plus `E_KLF12_HIGH` and four interface relays",
            current,
        )
        self.assertEqual(
            n - CURRENT["input_nodes"], len(CURRENT["free_non_input_nodes"])
        )
        summary = NETWORK_SIDECAR["summary"]
        self.assertEqual(NETWORK_SIDECAR["model_version"], CURRENT_VERSION)
        self.assertEqual(summary["dependencies"], CURRENT["dependencies"])
        self.assertIn(
            f"**{summary['absorbed_or_never_binding_dependencies']} of "
            f"{CURRENT['dependencies']} dependencies are absorbed or never bind** "
            f"({summary['absorbed_dependencies']} absorbed, "
            f"{summary['never_binding_inhibitions']} inhibitions that never bind)",
            current,
        )
        inert = CURRENT["phenotype_inert_nodes"]
        self.assertIn(
            f"**{len(inert)} nodes cannot change any phenotype output**", current
        )
        for node in ("E_PAEP", "S_IGFBP1", "S_PRL"):
            self.assertIn(node, inert)
        unread = CURRENT["unread_inputs"]
        self.assertIn(f"**{len(unread)} declared inputs are read by no rule**", current)
        for node in unread:
            self.assertIn(f"`{node}`", current)

    def test_quoted_alias_classes_are_current_v060_classes(self) -> None:
        current, _historical = _structure_parts()
        classes = [set(c) for c in CURRENT["alias_classes"]]
        quoted = re.findall(r"`([A-Za-z0-9_]+(?: = [A-Za-z0-9_]+)+)`", current)
        self.assertTrue(quoted)
        # Each quoted equality chain must lie inside one current class, and
        # adjacent chains joined by "now also equals" must too.
        for chain in quoted:
            members = {m.strip() for m in chain.split("=")}
            self.assertTrue(any(members <= c for c in classes), chain)
        self.assertIn(
            {
                "E_LIF",
                "E_GP130_STAT3",
                "E_CD98_CD9",
                "E_RECEPTIVE_SURFACE",
                "OUT_EPITHELIAL_RECEPTIVE",
            },
            classes,
        )
        progesterone = (
            "`IN_PROGESTIN = E_PGR = E_IHH = S_PGR = S_NR2F2 = S_BMP2 = S_HAND2`"
        )
        self.assertIn(progesterone, current)
        self.assertIn(
            {"IN_PROGESTIN", "E_PGR", "E_IHH", "S_PGR", "S_NR2F2", "S_BMP2", "S_HAND2"},
            classes,
        )
        secretory = next(c for c in classes if "E_PAEP" in c)
        self.assertIn(f"{len(secretory)}-member epithelial secretory class", current)
        decidual = next(c for c in classes if "S_PRL" in c)
        self.assertIn("S_IGFBP1", decidual)
        words = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}
        self.assertIn(
            f"`S_IGFBP1 = S_PRL` and {words[len(decidual) - 2]} more nodes", current
        )

    def test_current_summary_does_not_quote_the_superseded_u5_state(self) -> None:
        """Regression: the README once called v0.6.0 current while quoting 59/2^19/97."""
        current, _historical = _structure_parts()
        old = AUDIT["audited"]["structural"]["summary"]
        dead = AUDIT["audited"]["structural"]["absorbed_or_never_binding_dependencies"]
        for stale, now in (
            (f"2^{old['free_variables']}", f"2^{CURRENT['free_variables']}"),
            (f"{old['nodes']} named nodes", f"{CURRENT['nodes']} named nodes"),
            (
                f"of {old['dependencies']} dependencies",
                f"of {CURRENT['dependencies']} dependencies",
            ),
            (f"{dead} of ", None),
            (
                f"{old['distinct_functions']} distinct",
                f"{CURRENT['distinct_composed_functions']} distinct",
            ),
        ):
            if stale != now:
                self.assertNotIn(stale, current, stale)

    def test_historical_u5_numbers_are_labelled_and_match_the_audit(self) -> None:
        _current, historical = _structure_parts()
        structural = AUDIT["audited"]["structural"]
        summary = structural["summary"]
        self.assertIn(
            f"**{summary['nodes']} named nodes implement {summary['distinct_functions']} "
            "distinct Boolean functions**",
            historical,
        )
        dead = structural["absorbed_or_never_binding_dependencies"]
        self.assertIn(
            f"**{dead} of {summary['dependencies']} dependencies**", historical
        )
        self.assertIn(
            f"{summary['phenotype_inert_nodes']} nodes cannot change", historical
        )
        self.assertIn(
            f"all 2^{summary['free_variables']} free-variable assignments", historical
        )
        v052 = STRUCTURE["versions"]["adoc-literature-superset-v0.5.2"]
        self.assertIn(
            f"same {v052['nodes']}-node set and every composed function", historical
        )
        self.assertEqual(
            v052["nodes"], AUDIT["audited"]["structural"]["summary"]["nodes"]
        )
        self.assertIn(f"then {v052['dependencies']};", historical)
        self.assertIn(f"then {len(v052['phenotype_inert_nodes'])} nodes.", historical)
        ceilings = AUDIT["audited"]["identifiability"]["ceilings"]
        self.assertIn(
            f"**{ceilings['observation_classes_assayable_ceiling']} of "
            f"{ceilings['observation_classes_ceiling']}**",
            historical,
        )
        self.assertIn(
            f"{ceilings['design_states_now']} design-effective states out of "
            f"{ceilings['design_states_ceiling']}",
            historical,
        )
        self.assertIn("**not recomputed** for `v0.5.2` or `v0.6.0`", historical)

    def test_figure_versions_are_stated(self) -> None:
        table = README[README.index("## Where the project stands") :]
        table = _flat(table[: table.index("## What is measured")])
        self.assertIn(
            "the network overview and the exploratory dynamics animation are rendered "
            "from `v0.6.0`; the functional-endpoint figure stays a historical `v0.5.0` "
            "render",
            table,
        )
        endpoint = README[
            README.index("## The functional endpoint against experiment") :
        ]
        endpoint = _flat(endpoint[: endpoint.index("## Exploratory dynamics")])
        self.assertIn(
            "**A historical `v0.5.0` render; not regenerated for `v0.6.0`.**", endpoint
        )
        checks = _flat(README[README.index("## Checks") :])
        self.assertIn(
            "`u5-structural-audit` does **not** produce the current `v0.6.0` counts",
            checks,
        )

    def test_the_hand_set_endpoint_identity_matches_the_decomposition(self) -> None:
        endpoint = AUDIT["audited"]["identifiability"]["adhesion_endpoint"]
        p1, p2 = (endpoint["carrier_priors"][n] for n in endpoint["carrier_relays"])
        self.assertIn(
            f"`1 − (1 − {p1:.2f})(1 − {p2:.2f}) = {endpoint['analytic_value']:.2f}`",
            README,
        )

    def test_the_separating_dropouts_match_the_design_alias_rerun(self) -> None:
        gains = AUDIT["audited"]["design_alias"]["as_declared"]["candidate_gains"]
        separating = {c[0].split("__")[0]: c[1] for c in gains if c[2]}
        self.assertEqual(separating, {"dropout_IN_E2": 3, "dropout_IN_cAMP": 2})
        self.assertIn("(+3 against +2)", README)


if __name__ == "__main__":
    unittest.main()
