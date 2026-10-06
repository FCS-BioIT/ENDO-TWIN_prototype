"""Behavioural tests for the identifiability-design generator.

The claims these pin are the ones the companion document ranks designs on, so a
silent change in any of them would change an experimental recommendation.

The distinction under test throughout is the one the unit exists to keep:
**structural resolvability is not experimental yield.**
`test_no_single_veto_design_resolves_an_alias_pair` and
`test_a_resolved_pair_has_both_vetoes_run` are the regression tests for the two
errors independent review caught: counting pairs a panel makes resolvable as
pairs an experiment resolves, and crediting a pair when only one of its two
interventions is run.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

from dt_adoc.model.provenance import repo_root
from dt_adoc.perturbations.adjudication import AUDIT_MODEL_VERSION
from dt_adoc.reporting import identifiability_design as idd

ROOT: Path = repo_root()


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.analysis = idd.Analysis(AUDIT_MODEL_VERSION, ROOT)
        cls.pairs = cls.analysis.alias_pairs()

    # -- agreement with the committed artefact -------------------------------

    def test_reproduces_committed_expressivity_classes(self) -> None:
        """The baseline partition must match `v060_veto_expressivity.tsv`."""
        groups = self.analysis.groups(self.analysis.observed)
        non_null = {k for k in groups if k != "null"}
        self.assertEqual(len(non_null), 5)
        self.assertEqual(len(groups["null"]), 9)
        self.assertEqual(
            set(groups["E_LIF"]),
            {
                "E_GP130_STAT3",
                "E_LIF",
                "E_PC6",
                "S_HAND2",
                "S_TAZ_ECM",
                "hand2_loss",
            },
        )

    # -- target deduplication ------------------------------------------------

    def test_same_target_arms_are_not_counted_as_an_alias(self) -> None:
        """`hand2_loss` is `S_HAND2`, not a mechanism confusable with it."""
        formed = {(p["target_a"], p["target_b"]) for p in self.pairs}
        for a, b in formed:
            self.assertNotIn(
                {a, b},
                ({"S_HAND2", "hand2_loss"}, {"X_SPP1_LUMEN_FREE", "anti_spp1"}),
            )
        self.assertEqual(self.analysis.canon["hand2_loss"], "S_HAND2")
        self.assertEqual(self.analysis.canon["anti_spp1"], "X_SPP1_LUMEN_FREE")

    # -- collapse taxonomy ---------------------------------------------------

    def test_gp130_lif_pair_is_separable_only_at_targets(self) -> None:
        """The bare chain `E_GP130_STAT3 := E_LIF` has no distinct consequence.

        If this ever becomes `separable_downstream`, the rule changed and §1.3a
        of the companion document no longer describes the model.
        """
        row = self._pair("E_GP130_STAT3", "E_LIF")
        self.assertEqual(row["collapse_reason"], "separable_only_at_targets")
        self.assertEqual(row["separating_nodes"], "E_LIF")

    def test_a2_pair_has_no_downstream_separator(self) -> None:
        row = self._pair("E_ITGAVB3_5", "X_SPP1_LUMEN_FREE")
        self.assertEqual(row["collapse_reason"], "separable_only_at_targets")
        self.assertEqual(row["separating_nodes_beyond_targets"], "")

    def test_every_pair_carries_a_known_reason(self) -> None:
        allowed = {
            "rule_identical_everywhere",
            "separable_only_at_targets",
            "separable_downstream",
        }
        self.assertTrue(self.pairs)
        for row in self.pairs:
            self.assertIn(row["collapse_reason"], allowed)

    # -- the error an independent review caught ------------------------------

    def test_no_single_veto_design_resolves_an_alias_pair(self) -> None:
        """One arm cannot de-alias two interventions.

        Regression test for two errors review caught: counting structural
        resolvability as experimental yield, and crediting a pair when only one
        of its two vetoes is run.
        """
        for row in self.analysis.design_yield(self.pairs):
            arms = set(row["veto_arms_run"].split(";")) - {"(none)"}
            if len(arms) < 2:
                self.assertEqual(
                    row["alias_pairs_resolved"],
                    "0",
                    f"{row['design']} claims to de-alias from {len(arms)} arm(s)",
                )

    def test_a_resolved_pair_has_both_vetoes_run(self) -> None:
        for row in self.analysis.design_yield(self.pairs):
            arms = set(row["veto_arms_run"].split(";")) - {"(none)"}
            if row["alias_pairs_resolved_detail"] == "(none)":
                continue
            for pair in row["alias_pairs_resolved_detail"].split(";"):
                self.assertTrue(
                    set(pair.split("|")) <= arms,
                    f"{row['design']} credits {pair} without running both vetoes",
                )

    def test_variant_counts_are_distinct_variants_not_variant_arm_pairs(self) -> None:
        """One variant read under two arms is ONE variant discriminated.

        Counting `variant@arm` labels inflated every multi-arm design and the
        ranking was built on that number.
        """
        for row in self.analysis.design_yield(self.pairs):
            for count_key, detail_key in (
                (
                    "variants_discriminated_within_design",
                    "variants_within_design_detail",
                ),
                (
                    "variants_needing_an_extra_input_arm",
                    "variants_needing_extra_arm_detail",
                ),
            ):
                detail = row[detail_key]
                if detail == "(none)":
                    self.assertEqual(row[count_key], "0")
                    continue
                ids = {entry.split("@")[0] for entry in detail.split(";")}
                self.assertEqual(
                    int(row[count_key]),
                    len(ids),
                    f"{row['design']}/{row['latent_scenario']} {count_key} "
                    f"disagrees with {len(ids)} distinct variants in {detail}",
                )

    def test_within_and_extra_arm_columns_are_disjoint(self) -> None:
        """A variant discriminated under the design does not need an extra arm.

        The two columns partition the variants a design touches. Leaving a
        variant in both made "needing an extra input arm" false for it and
        double-counted it across the pair.
        """
        for row in self.analysis.design_yield(self.pairs):
            within = {
                e.split("@")[0] for e in row["variants_within_design_detail"].split(";")
            } - {"(none)"}
            extra = {
                e.split("@")[0]
                for e in row["variants_needing_extra_arm_detail"].split(";")
            } - {"(none)"}
            self.assertEqual(
                within & extra,
                set(),
                f"{row['design']}/{row['latent_scenario']} lists "
                f"{sorted(within & extra)} as both discriminated and needing an "
                "extra arm",
            )

    def test_two_arm_design_does_not_double_count_one_variant(self) -> None:
        """Design 6 reads CD98-c under both arms; that is one variant."""
        rows = {
            (r["design"], r["latent_scenario"]): r
            for r in self.analysis.design_yield(self.pairs)
        }
        row = rows[("6_two_arm_stat3_and_lif", "E_KLF12_HIGH=low")]
        self.assertEqual(row["variants_discriminated_within_design"], "1")
        self.assertIn("CD98-c@", row["variants_within_design_detail"])

    def test_yield_is_reported_per_condition_and_scenario(self) -> None:
        """No yield may be unioned over conditions or latent scenarios."""
        rows = self.analysis.design_yield(self.pairs)
        scenarios = {r["latent_scenario"] for r in rows}
        self.assertEqual(len(scenarios), len(self.analysis.scenarios))
        self.assertIn("E_KLF12_HIGH=high", scenarios)
        for row in rows:
            self.assertEqual(row["execution_context"], idd.EXECUTION_CONTEXT)

    def test_klf12_scenario_changes_a_reported_yield(self) -> None:
        """The latent matters, so reporting one value would have hidden it."""
        rows = {
            (r["design"], r["latent_scenario"]): r
            for r in self.analysis.design_yield(self.pairs)
        }
        low = rows[("2_pc6_veto", "E_KLF12_HIGH=low")]
        high = rows[("2_pc6_veto", "E_KLF12_HIGH=high")]
        self.assertNotEqual(
            low["variants_discriminated_within_design"],
            high["variants_discriminated_within_design"],
        )

    def test_structural_resolvability_exceeds_experimental_yield(self) -> None:
        """Panel B makes 31 pairs resolvable; no single-veto design resolves 31."""
        panels = {
            r["panel"]: r for r in self.analysis.panel_structural_value(self.pairs)
        }
        structural = int(
            panels["B_A_plus_free_spp1"]["alias_pairs_made_resolvable_structural"]
        )
        self.assertEqual(structural, 31)
        best = max(
            int(r["alias_pairs_resolved"])
            for r in self.analysis.design_yield(self.pairs)
        )
        self.assertLess(best, structural)

    # -- variant semantics ---------------------------------------------------

    def test_stat3_and_lif_arms_are_never_merged(self) -> None:
        """Under `GP130-b` a LIF veto discriminates and a STAT3 veto does not.

        A row naming both arms at once would be false for one of them.
        """
        rows = self.analysis.variant_arm_discrimination()
        gp130 = [
            r
            for r in rows
            if r["variant_id"] == "GP130-b" and r["extra_free_inputs"] == "X_IL11=on"
        ]
        arms = {r["perturbation_arm"] for r in gp130}
        self.assertIn("veto:E_LIF", arms)
        self.assertNotIn("veto:E_GP130_STAT3", arms)

    def test_every_variant_is_registered_not_invented(self) -> None:
        """No variant may appear that the repository does not register.

        Exactly two permitted sources: the **seven** non-baseline Gate-3
        variants registered against v0.4.0 and mechanically transported under
        exact baseline-rule identity, and the non-default rows registered
        directly in this model's own `rule_variants.tsv`. Anything else would be
        a variant this analysis made up in order to score it.
        """
        import csv as _csv

        from dt_adoc.experiments.variant_discrimination import VARIANTS
        from dt_adoc.model.runtime import resolve_model

        registered = {v.variant_id for v in VARIANTS}
        spec = resolve_model(AUDIT_MODEL_VERSION, ROOT)
        catalogue = spec.network_bnd.parent / "rule_variants.tsv"
        with catalogue.open(encoding="utf-8", newline="") as handle:
            registered |= {
                r["variant_id"]
                for r in _csv.DictReader(handle, delimiter="\t")
                if r["status"] != "default_executable"
            }
        rows = self.analysis.variant_arm_discrimination()
        self.assertTrue(rows)
        for row in rows:
            self.assertIn(row["variant_id"], registered)

    def test_default_executable_rows_are_not_treated_as_variants(self) -> None:
        """`default_executable` IS the committed rule, so it differs by nothing."""
        ids = {r["variant_id"] for r in self.analysis.variant_arm_discrimination()}
        self.assertNotIn("adoc_literature_superset_v040", ids)

    def test_gate3_transport_requires_identical_baseline_rules(self) -> None:
        """A v0.4 variant may only transport where its baseline rule is unchanged.

        A variant says "the committed rule, versus this alternative". If the
        committed rule has changed between the Gate-3 source model and the one
        under analysis, the transported variant would be compared against a
        baseline that no longer exists.
        """
        from dt_adoc.experiments import variant_discrimination as gate3
        from dt_adoc.model.runtime import resolve_model
        from dt_adoc.reporting import veto_expressivity as vx

        overridden = {node for v in gate3.VARIANTS for node in (v.overrides or {})}
        self.assertEqual(
            overridden,
            {
                "E_CD98_CD9",
                "E_CDH1_APICAL",
                "E_GP130_STAT3",
                "E_DAG1_CLEAVED",
                "E_DAG1_FULL",
            },
            "the set of transported nodes changed; re-check the guard",
        )
        source = vx.parse_network(
            resolve_model(gate3.MODEL_VERSION, ROOT).network_bnd.read_text(
                encoding="utf-8"
            )
        ).rules
        current = vx.parse_network(
            resolve_model(AUDIT_MODEL_VERSION, ROOT).network_bnd.read_text(
                encoding="utf-8"
            )
        ).rules
        for node in sorted(overridden):
            self.assertEqual(
                source[node],
                current[node],
                f"{node} baseline differs between {gate3.MODEL_VERSION} and "
                f"{AUDIT_MODEL_VERSION}; transport must be refused, not adjusted",
            )

    def test_transport_is_refused_when_a_baseline_rule_differs(self) -> None:
        """The guard must fail closed, not fall back to transporting anyway."""
        from dt_adoc.reporting import veto_expressivity as vx

        real = vx.parse_network
        calls = {"n": 0}

        def fake(text: str):
            # Perturb the SECOND parse (the current model) so the two disagree.
            network = real(text)
            calls["n"] += 1
            if calls["n"] == 2:
                rules = dict(network.rules)
                rules["E_GP130_STAT3"] = "(E_LIF) and (E_PC6)"
                return vx.Network(network.order, rules, network.free, network.nodes)
            return network

        vx.parse_network = fake
        try:
            with self.assertRaises(idd.ExpressivityConfigError) as caught:
                idd._registered_variants(ROOT, {"E_CD98_CD9", "E_GP130_STAT3"})
            self.assertIn("E_GP130_STAT3", str(caught.exception))
        finally:
            vx.parse_network = real

    def test_klf12_is_a_latent_scenario_not_a_panel_readout(self) -> None:
        """`E_KLF12_HIGH` is represented but has no validated observation mapping.

        Four assertions, because the prose conclusion and the machine-readable
        assayability must agree and the arithmetic must not move.

        1. It is not currently assayable. `candidate_readouts.tsv` marks it
           `true` — correctly, for its own narrower question, since the KLF12
           transcript is measurable — so this analysis overrides it with a
           provenance-cited third value. `docs/scrna/klf12_prior_finding.md`
           records that the existing scRNA establishes no interpretable
           high/low boundary and no measured prior.
        2. It appears in no measurement panel.
        3. Both latent scenarios survive: excluding it as a *readout* must not
           collapse it as a *state*.
        4. No alias, variant-yield or recommendation arithmetic changes.
        """
        # 1 — not currently assayable, and the override cites its basis
        self.assertEqual(
            self.analysis.assayable["E_KLF12_HIGH"],
            idd.BLOCKED_NO_VALIDATED_MAPPING,
        )
        value, basis = idd.ASSAYABILITY_OVERRIDES["E_KLF12_HIGH"]
        self.assertEqual(value, idd.BLOCKED_NO_VALIDATED_MAPPING)
        self.assertTrue((ROOT / basis).exists(), f"{basis} must exist")

        # 2 — in no panel, and excluded from the minimal-panel search
        for name, _, _ in idd.PANELS:
            self.assertNotIn("E_KLF12_HIGH", idd._panel_readouts(name))
        for row in self.analysis.minimal_identifying_panel(self.pairs):
            self.assertNotIn("E_KLF12_HIGH", row["minimal_panel"])

        # 3 — both latent scenarios remain
        self.assertEqual(
            {
                self.analysis.scenario_label(i)
                for i in range(len(self.analysis.scenarios))
            },
            {"E_KLF12_HIGH=low", "E_KLF12_HIGH=high"},
        )

        # 4 — arithmetic pinned
        self.assertEqual(len(self.pairs), 48)
        groups = self.analysis.groups(self.analysis.observed)
        self.assertEqual(len([k for k in groups if k != "null"]), 5)
        self.assertEqual(len(groups["null"]), 9)
        panels = {
            r["panel"]: r for r in self.analysis.panel_structural_value(self.pairs)
        }
        self.assertEqual(
            [
                panels[name]["alias_pairs_made_resolvable_structural"]
                for name, _, _ in idd.PANELS
            ],
            ["0", "30", "31", "38", "40", "42", "42"],
        )
        yields = {
            (r["design"], r["latent_scenario"]): (
                r["alias_pairs_resolved"],
                r["variants_discriminated_within_design"],
            )
            for r in self.analysis.design_yield(self.pairs)
        }
        self.assertEqual(yields[("3_hand2_veto", "E_KLF12_HIGH=low")], ("0", "1"))
        self.assertEqual(yields[("3_hand2_veto", "E_KLF12_HIGH=high")], ("0", "2"))
        self.assertEqual(yields[("4_stat3_veto", "E_KLF12_HIGH=low")], ("0", "1"))
        self.assertEqual(yields[("5_lif_veto", "E_KLF12_HIGH=low")], ("0", "1"))
        self.assertEqual(
            yields[("6_two_arm_stat3_and_lif", "E_KLF12_HIGH=low")], ("1", "1")
        )
        self.assertEqual(
            yields[("1_readout_only_existing_arms", "E_KLF12_HIGH=low")], ("0", "0")
        )

    def test_all_registered_gate3_variants_appear(self) -> None:
        """A variant exposed only by an unexercised input must still be covered.

        `CD98-b`, `CD98-d` and `CDH1-c` read `IN_HCG` or
        `IN_EMBRYO_CONDITIONED_SIGNAL`, which no recorded arm turns on. Carrying
        only `required_inputs` made them vanish from the table entirely.
        """
        from dt_adoc.experiments.variant_discrimination import VARIANTS

        present = {r["variant_id"] for r in self.analysis.variant_arm_discrimination()}
        for variant in VARIANTS:
            if not variant.overrides:
                continue
            self.assertIn(variant.variant_id, present)

    def test_controlled_input_defaults_decide_current_design(self) -> None:
        """`E_DAG1_CLEAVABLE = off` is the intervention, not the status quo."""
        rows = [
            r
            for r in self.analysis.variant_arm_discrimination()
            if r["variant_id"] == "PC6-b"
        ]
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(row["extra_free_inputs"], "E_DAG1_CLEAVABLE=off")
            self.assertEqual(row["setting_is_current_design"], "no")

    def test_literature_parity_variant_needs_the_klf12_high_scenario(self) -> None:
        """Fixing scenarios[0] hid this variant completely."""
        rows = [
            r
            for r in self.analysis.variant_arm_discrimination()
            if r["variant_id"] == "literature_parity_v020"
        ]
        self.assertTrue(rows)
        self.assertEqual({r["scenario"] for r in rows}, {"E_KLF12_HIGH=high"})

    def test_il11_anxa2_executor_is_not_scored(self) -> None:
        """The repository refuses to write it; this module must not resurrect it."""
        for row in self.analysis.variant_arm_discrimination():
            self.assertNotIn("E_ANXA2_ACTIN :=", row["rule_change"])

    def test_minimal_panel_is_minimal_and_sufficient(self) -> None:
        """Each reported panel separates every rival, and nothing smaller does."""
        import itertools as it

        rows = self.analysis.minimal_identifying_panel(self.pairs)
        self.assertTrue(rows)
        for row in rows:
            if not row["panel_size"]:
                continue
            panel = row["minimal_panel"].split(";")
            rivals = row["rivals_in_class"].split(";")
            for rival in rivals:
                self.assertTrue(
                    any(
                        self.analysis.separates(row["target"], rival, n) for n in panel
                    ),
                    f"{row['target']} panel fails against {rival}",
                )
            for smaller in range(1, len(panel)):
                for combo in it.combinations(panel, smaller):
                    self.assertFalse(
                        all(
                            any(
                                self.analysis.separates(row["target"], rival, n)
                                for n in combo
                            )
                            for rival in rivals
                        ),
                        f"{row['target']} panel is not minimal: {combo} suffices",
                    )

    def test_pstat3_alone_cannot_identify_the_gp130_arm(self) -> None:
        """`E_GP130_STAT3` needs `E_LIF` beside it; pSTAT3 alone is not enough.

        This is the claim §6 of the companion document turns on.
        """
        rows = {
            r["target"]: r for r in self.analysis.minimal_identifying_panel(self.pairs)
        }
        panel = rows["E_GP130_STAT3"]["minimal_panel"].split(";")
        self.assertIn("E_LIF", panel)
        self.assertFalse(
            self.analysis.separates("E_GP130_STAT3", "E_LIF", "E_GP130_STAT3")
        )

    # -- panel definitions ---------------------------------------------------

    def test_panels_are_nested(self) -> None:
        previous: tuple[str, ...] = ()
        for name, _, _ in idd.PANELS:
            current = idd._panel_readouts(name)
            self.assertEqual(
                set(previous) - set(current),
                set(),
                f"panel {name} drops a readout its predecessor had",
            )
            previous = current

    def test_taz_panel_adds_nothing(self) -> None:
        """Panel F is on the frontier only as a demonstration that it is wasted."""
        panels = {
            r["panel"]: r for r in self.analysis.panel_structural_value(self.pairs)
        }
        self.assertEqual(
            panels["F_E_plus_taz"]["alias_pairs_made_resolvable_structural"],
            panels["E_D_plus_proliferation"]["alias_pairs_made_resolvable_structural"],
        )

    def _pair(self, a: str, b: str) -> dict[str, str]:
        for row in self.pairs:
            if {row["target_a"], row["target_b"]} == {a, b}:
                return row
        raise AssertionError(f"no alias pair {a}|{b}")


class DocumentedCommandTests(unittest.TestCase):
    """The command the companion document gives must be the one that works.

    An earlier revision documented a bare ``python -m`` invocation. The
    generator reads the Gate-3 variant registry, whose module imports PyYAML,
    so outside the locked environment that command raises rather than
    reproducing the committed tables.
    """

    def test_doc_registers_the_pixi_tasks_it_names(self) -> None:
        pixi = (ROOT / "pixi.toml").read_text(encoding="utf-8")
        doc = (ROOT / "docs/identifiability_experiment_design.md").read_text(
            encoding="utf-8"
        )
        for task in ("identifiability-design", "identifiability-design-check"):
            self.assertIn(f"[tasks.{task}]", pixi)
            self.assertIn(f"pixi run {task}", doc)

    def test_doc_does_not_document_a_bare_interpreter_command(self) -> None:
        doc = (ROOT / "docs/identifiability_experiment_design.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("python -m dt_adoc.reporting.identifiability_design", doc)

    def test_stated_table_count_matches_build(self) -> None:
        """The pixi description and module docstring must state what build() emits."""
        produced = [str(path) for path, _ in idd.build(root=ROOT)]
        self.assertEqual(len(produced), 7)
        pixi = (ROOT / "pixi.toml").read_text(encoding="utf-8")
        self.assertIn("all seven docs/identifiability_design/ tables", pixi)
        docstring = idd.__doc__ or ""
        self.assertIn("Seven tables are produced.", docstring)
        for path in produced:
            self.assertIn(Path(path).name, docstring, f"{path} missing from docstring")

    def test_registered_tasks_invoke_this_module(self) -> None:
        pixi = (ROOT / "pixi.toml").read_text(encoding="utf-8")
        self.assertIn(
            "python -B -m dt_adoc.reporting.identifiability_design write", pixi
        )
        self.assertIn(
            "python -B -m dt_adoc.reporting.identifiability_design check", pixi
        )


class VariantSourceTests(unittest.TestCase):
    def test_missing_transitive_dependency_fails_closed(self) -> None:
        """A variant-source import failure must raise, never degrade silently.

        Swallowing it emitted a variant-free table and reported the committed
        artefacts stale, which is the opposite of what a provenance check is
        for.

        Run in a SUBPROCESS. The Gate-3 module reaches PyYAML through
        intermediate ``dt_adoc`` modules, so evicting it from ``sys.modules``
        in-process is not enough — the intermediates stay cached, the import
        succeeds, and the patch silently tests nothing. A fresh interpreter is
        also the condition under which the failure actually happens.
        """
        script = textwrap.dedent(
            """
            import sys

            class Blocker:
                def find_spec(self, name, path=None, target=None):
                    if name == "yaml" or name.startswith("yaml."):
                        raise ModuleNotFoundError("No module named 'yaml'", name="yaml")
                    return None

            sys.meta_path.insert(0, Blocker())
            from dt_adoc.reporting import identifiability_design as idd
            from pathlib import Path
            try:
                idd._registered_variants(Path(sys.argv[1]), {"E_CD98_CD9"})
            except ModuleNotFoundError as error:
                print("RAISED", error.name)
            except idd.ExpressivityConfigError:
                print("RAISED refused")
            else:
                print("DEGRADED")
            """
        )
        env = dict(
            os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1"
        )
        result = subprocess.run(
            [sys.executable, "-c", script, str(ROOT)],
            capture_output=True,
            text=True,
            env=env,
            cwd=ROOT,
            check=False,
        )
        self.assertIn("RAISED", result.stdout, result.stdout + result.stderr)
        self.assertNotIn("DEGRADED", result.stdout)


class ArtifactCurrencyTests(unittest.TestCase):
    def test_committed_tables_are_current(self) -> None:
        """`check` must fail if any committed table is stale."""
        for path, text in idd.build(root=ROOT):
            target = ROOT / path
            self.assertTrue(target.exists(), f"{path} is missing")
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                text,
                f"{path} is stale; run `pixi run identifiability-design`",
            )


if __name__ == "__main__":
    unittest.main()
