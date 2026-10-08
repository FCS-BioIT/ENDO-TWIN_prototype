"""Stage 2 of the intervention-layer refactor, statically: the legacy-route rendering.

``legacy_route_overrides`` and the runner helpers that feed it. The runtime gate
(G7) is ``tests/integration/test_intervention_routing_runtime.py``.
"""

from __future__ import annotations

import dataclasses
import itertools
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.maboss_adapter import LOGIC_LINE_RE, NODE_BLOCK_RE
from dt_adoc.model.runtime import resolve_model
from dt_adoc.perturbations.engine import (
    ACTIVITY_VETO,
    InterventionError,
    intervention_logic_overrides,
    legacy_route_overrides,
    load_intervention_library,
)
from dt_adoc.simulation import runner
from dt_adoc.simulation.runner import ContinuationState

MODEL_VERSION = "adoc-literature-superset-v0.5.2"
LEGACY_INPUTS = ("IN_MIFEPRISTONE", "IN_ANTI_SPP1", "IN_HAND2_LOSS")
TARGETS = {"E_PGR", "S_PGR", "X_SPP1_LUMEN_FREE", "S_HAND2"}
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _rules(network_text: str) -> dict[str, str]:
    rules = {}
    for match in NODE_BLOCK_RE.finditer(network_text):
        (logic,) = LOGIC_LINE_RE.findall(match.group(3))
        rules[match.group(2)] = logic[1].strip()
    return rules


def _names(logic: str) -> set[str]:
    return set(IDENTIFIER.findall(logic)) - {"and", "or", "not"}


def _evaluate(logic: str, point: dict[str, bool]) -> bool:
    return bool(eval(logic, {"__builtins__": {}}, dict(point)))


class LegacyRouteOverridesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.library = load_intervention_library(ROOT)
        cls.network_text = resolve_model(MODEL_VERSION, ROOT).network_bnd.read_text(
            encoding="utf-8"
        )
        cls.rules = _rules(cls.network_text)

    def overrides(self, values: dict[str, bool], **kwargs) -> dict[str, str]:
        return legacy_route_overrides(
            kwargs.get("text", self.network_text),
            values,
            model_version=MODEL_VERSION,
            library=kwargs.get("library", self.library),
        )

    def test_every_combination_of_legacy_inputs_is_equivalent(self) -> None:
        """Checked here independently of the engine's own check, for all eight
        combinations, including ones no protocol declares."""
        for values in itertools.product((False, True), repeat=len(LEGACY_INPUTS)):
            inputs = dict(zip(LEGACY_INPUTS, values))
            overrides = self.overrides(inputs)
            self.assertEqual(set(overrides), TARGETS)
            for target, rendered in overrides.items():
                legacy = self.rules[target]
                self.assertFalse(_names(rendered) & set(LEGACY_INPUTS), target)
                free = sorted((_names(legacy) | _names(rendered)) - set(LEGACY_INPUTS))
                for point_values in itertools.product((False, True), repeat=len(free)):
                    point = {**dict(zip(free, point_values)), **inputs}
                    self.assertEqual(
                        _evaluate(rendered, point), _evaluate(legacy, point), target
                    )

    def test_an_inactive_intervention_only_disconnects_its_input(self) -> None:
        overrides = self.overrides(dict.fromkeys(LEGACY_INPUTS, False))
        self.assertEqual(overrides["E_PGR"], "IN_PROGESTIN and not 0")
        self.assertEqual(overrides["S_HAND2"], "(S_BMP2 or S_PGR) and not 0")
        for rendered in overrides.values():
            self.assertNotIn("and not 1", rendered)

    def test_an_active_intervention_vetoes_exactly_its_targets(self) -> None:
        overrides = self.overrides(
            {"IN_MIFEPRISTONE": True, "IN_ANTI_SPP1": False, "IN_HAND2_LOSS": False}
        )
        vetoed = {
            node for node, logic in overrides.items() if logic.endswith("and not 1")
        }
        self.assertEqual(vetoed, {"E_PGR", "S_PGR"})
        self.assertEqual(overrides["E_PGR"], "(IN_PROGESTIN and not 0) and not 1")

    def test_xav939_needs_no_value_and_renders_nothing(self) -> None:
        overrides = self.overrides(dict.fromkeys(LEGACY_INPUTS, True))
        self.assertTrue(all("IN_XAV939" not in logic for logic in overrides.values()))

    def test_a_missing_input_value_is_refused(self) -> None:
        with self.assertRaises(InterventionError):
            self.overrides({"IN_MIFEPRISTONE": False, "IN_ANTI_SPP1": False})

    def test_a_legacy_input_read_other_than_as_a_veto_is_refused(self) -> None:
        """If a rule used the input as an activator, disconnecting it would change
        the model, and the engine must refuse rather than render it."""
        text = self.network_text.replace(
            "logic = IN_PROGESTIN and not IN_MIFEPRISTONE;",
            "logic = IN_PROGESTIN or IN_MIFEPRISTONE;",
            1,
        )
        self.assertNotEqual(text, self.network_text)
        # Refused even in a phase where the input is off, where the rendering
        # would happen to agree: the mapping itself is wrong.
        with self.assertRaisesRegex(InterventionError, "not equivalent"):
            self.overrides(dict.fromkeys(LEGACY_INPUTS, False), text=text)

    def test_an_unreadable_rule_is_refused(self) -> None:
        text = self.network_text.replace(
            "logic = IN_PROGESTIN and not IN_MIFEPRISTONE;",
            "logic = IN_PROGESTIN & !IN_MIFEPRISTONE;",
            1,
        )
        with self.assertRaises(InterventionError):
            self.overrides(dict.fromkeys(LEGACY_INPUTS, False), text=text)

    def test_a_legacy_input_that_is_not_a_constant_input_is_refused(self) -> None:
        for replacement in (
            "IN_MIFEPRISTONE or IN_E2",
            "IN_MIFEPRISTONE;\n  rate_down = 2",
        ):
            text = self.network_text.replace(
                "  logic = IN_MIFEPRISTONE;", f"  logic = {replacement};", 1
            )
            self.assertNotEqual(text, self.network_text)
            with self.assertRaisesRegex(InterventionError, "not a constant input"):
                self.overrides(dict.fromkeys(LEGACY_INPUTS, False), text=text)

    def test_other_model_versions_get_no_overrides(self) -> None:
        self.assertEqual(
            legacy_route_overrides(
                self.network_text,
                {},
                model_version="adoc-literature-superset-v0.5.1",
                library=self.library,
            ),
            {},
        )


class CompositionParityTest(unittest.TestCase):
    """The two composition paths must agree on which targets a set vetoes.

    ``intervention_logic_overrides`` composes against the model's own rules;
    the executed path composes against the Stage 2 *disconnected* rules, so the
    rendered strings differ by construction. What must not differ is which
    targets end up vetoed -- otherwise the documented rule and the executed one
    are two rules.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.library = load_intervention_library(ROOT)
        cls.network_text = resolve_model(MODEL_VERSION, ROOT).network_bnd.read_text(
            encoding="utf-8"
        )
        cls.vetoing = sorted(
            key
            for key, effects in cls.library.items()
            if effects[0].mode == ACTIVITY_VETO
        )

    def test_every_subset_vetoes_the_same_targets_on_both_paths(self) -> None:
        inert = [
            key
            for key, effects in self.library.items()
            if effects[0].mode != ACTIVITY_VETO
        ]
        members = self.vetoing + inert
        self.assertGreaterEqual(len(members), 4)
        quiet = dict.fromkeys(LEGACY_INPUTS, False)
        for size in range(len(members) + 1):
            for combination in itertools.combinations(members, size):
                with self.subTest(combination=combination):
                    documented = intervention_logic_overrides(
                        self.network_text,
                        list(combination),
                        model_version=MODEL_VERSION,
                        library=self.library,
                    )
                    executed = legacy_route_overrides(
                        self.network_text,
                        quiet,
                        model_version=MODEL_VERSION,
                        library=self.library,
                        also_active=combination,
                    )
                    vetoed = {
                        node
                        for node, logic in executed.items()
                        if logic.endswith("and not 1")
                    }
                    self.assertEqual(set(documented), vetoed)

    def test_a_target_is_never_vetoed_twice(self) -> None:
        """Both paths are idempotent, so no rendering carries a doubled veto."""
        quiet = dict.fromkeys(LEGACY_INPUTS, False)
        executed = legacy_route_overrides(
            self.network_text,
            quiet,
            model_version=MODEL_VERSION,
            library=self.library,
            also_active=tuple(self.vetoing),
        )
        for logic in executed.values():
            self.assertNotIn(") and not 1) and not 1", logic)

    def test_a_marker_and_a_name_cannot_double_veto(self) -> None:
        """With a marker already active, naming a *different* intervention leaves
        the marker's own target vetoed exactly once."""
        active = {**dict.fromkeys(LEGACY_INPUTS, False), "IN_HAND2_LOSS": True}
        executed = legacy_route_overrides(
            self.network_text,
            active,
            model_version=MODEL_VERSION,
            library=self.library,
            also_active=("mifepristone",),
        )
        self.assertTrue(executed["S_HAND2"].endswith("and not 1"))
        self.assertNotIn(") and not 1) and not 1", executed["S_HAND2"])
        self.assertTrue(executed["E_PGR"].endswith("and not 1"))


class RunnerRoutingHelpersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.network_text = resolve_model(MODEL_VERSION, ROOT).network_bnd.read_text(
            encoding="utf-8"
        )

    def merged_cfg(self, lines: list[str]) -> Path:
        path = self.tmp / "merged.cfg"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def overrides(self, cfg: Path, continuation=None, version=MODEL_VERSION):
        return self.routed(cfg, continuation, version)[0]

    def routed(self, cfg: Path, continuation=None, version=MODEL_VERSION):
        return runner._intervention_overrides(
            model_version=version,
            network_text=self.network_text,
            merged_cfg=cfg,
            continuation=continuation,
            root=ROOT,
        )

    def test_cfg_values_are_read_as_fixed_booleans(self) -> None:
        assignments = {
            "A.istate": "A.istate = TRUE;",
            "B.istate": "B.istate = 0;",
            "C.istate": "C.istate = 0.5;",
        }
        self.assertTrue(runner._cfg_input_value(assignments, "A"))
        self.assertFalse(runner._cfg_input_value(assignments, "B"))
        with self.assertRaises(InterventionError):
            runner._cfg_input_value(assignments, "C")
        with self.assertRaises(InterventionError):
            runner._cfg_input_value(assignments, "D")

    def test_forced_nodes_win_over_the_cfg(self) -> None:
        """forced_nodes are applied after the cfg, so they decide the value."""
        cfg = self.merged_cfg([f"{name}.istate = FALSE;" for name in LEGACY_INPUTS])
        continuation = ContinuationState(
            mode="joint",
            continuation_method="projected_joint_memory",
            forced_nodes={"IN_MIFEPRISTONE": True},
        )
        overrides = self.overrides(cfg, continuation)
        self.assertTrue(overrides["E_PGR"].endswith("and not 1"))
        self.assertFalse(overrides["S_HAND2"].endswith("and not 1"))
        self.assertFalse(self.overrides(cfg)["E_PGR"].endswith("and not 1"))

    def test_a_cfg_without_a_legacy_input_is_refused(self) -> None:
        cfg = self.merged_cfg(["IN_MIFEPRISTONE.istate = FALSE;"])
        with self.assertRaises(InterventionError):
            self.overrides(cfg)

    def test_legacy_routing_and_uncovered_models_render_nothing(self) -> None:
        cfg = self.merged_cfg([f"{name}.istate = TRUE;" for name in LEGACY_INPUTS])
        with mock.patch.object(runner, "INTERVENTION_ROUTING", "legacy"):
            self.assertEqual(self.routed(cfg), ({}, None, {}))
        overrides, library, values = self.routed(
            cfg, version="adoc-literature-superset-v0.5.1"
        )
        self.assertEqual(values, {})
        self.assertEqual(overrides, {})
        self.assertEqual(library["path"], "config/intervention_library.tsv")

    def test_an_unknown_routing_is_refused(self) -> None:
        cfg = self.merged_cfg([f"{name}.istate = TRUE;" for name in LEGACY_INPUTS])
        with (
            mock.patch.object(runner, "INTERVENTION_ROUTING", "fast"),
            self.assertRaises(ValueError),
        ):
            self.overrides(cfg)

    def test_continuations_decide_undeclared_inputs_as_maboss_does(self) -> None:
        """A marginal continuation carries every tracked node, IN_HAND2_LOSS among
        them since it is not internal; a joint one carries its memory nodes. Both
        win over the cfg unless the input is forced."""
        assignments = {"IN_HAND2_LOSS.istate": "IN_HAND2_LOSS.istate = FALSE;"}

        class FakeResult:
            def __init__(self, value):
                self.value = value

            def get_nodes_probtraj(self):
                import pandas

                return pandas.DataFrame({"IN_HAND2_LOSS": [self.value], "S_PGR": [0.4]})

        def marginal(value, forced=None):
            return ContinuationState(
                mode="marginal",
                continuation_method="node_marginals_independent",
                forced_nodes=forced or {},
                previous_result=FakeResult(value),
            )

        value = runner._legacy_input_value
        self.assertFalse(value("IN_HAND2_LOSS", assignments, None))
        self.assertTrue(value("IN_HAND2_LOSS", assignments, marginal(1.0)))
        self.assertFalse(
            value("IN_HAND2_LOSS", assignments, marginal(1.0, {"IN_HAND2_LOSS": False}))
        )
        with self.assertRaises(InterventionError):
            value("IN_HAND2_LOSS", assignments, marginal(0.5))
        joint = ContinuationState(
            mode="joint",
            continuation_method="projected_joint_memory",
            node_ids=("S_PGR", "IN_HAND2_LOSS"),
            distribution={(0, 1): 0.25, (1, 1): 0.75},
        )
        self.assertTrue(value("IN_HAND2_LOSS", assignments, joint))
        mixed = dataclasses.replace(joint, distribution={(0, 0): 0.25, (1, 1): 0.75})
        with self.assertRaises(InterventionError):
            value("IN_HAND2_LOSS", assignments, mixed)
        not_carried = dataclasses.replace(
            joint, node_ids=("S_PGR",), distribution={(1,): 1.0}
        )
        self.assertFalse(value("IN_HAND2_LOSS", assignments, not_carried))

    def test_a_jointly_set_legacy_input_is_refused(self) -> None:
        cfg = self.merged_cfg(
            [f"{name}.istate = FALSE;" for name in LEGACY_INPUTS]
            + ["[S_PGR, IN_HAND2_LOSS].istate = 1 [0, 1];"]
        )
        with self.assertRaises(InterventionError):
            self.overrides(cfg)

    def test_a_root_without_the_library_routes_nothing(self) -> None:
        cfg = self.merged_cfg([f"{name}.istate = TRUE;" for name in LEGACY_INPUTS])
        self.assertEqual(
            runner._intervention_overrides(
                model_version=MODEL_VERSION,
                network_text=self.network_text,
                merged_cfg=cfg,
                continuation=None,
                root=self.tmp,
            ),
            ({}, None, {}),
        )

    def test_naming_an_intervention_for_an_uncovered_model_is_refused(self) -> None:
        cfg = self.merged_cfg([f"{name}.istate = FALSE;" for name in LEGACY_INPUTS])
        with self.assertRaisesRegex(InterventionError, "covers no intervention"):
            runner._intervention_overrides(
                model_version="adoc-literature-superset-v0.5.1",
                network_text=self.network_text,
                merged_cfg=cfg,
                continuation=None,
                root=ROOT,
                interventions=("hand2_loss",),
            )

    def test_naming_an_intervention_without_a_library_is_refused(self) -> None:
        cfg = self.merged_cfg([f"{name}.istate = FALSE;" for name in LEGACY_INPUTS])
        with self.assertRaisesRegex(InterventionError, "no intervention library"):
            runner._intervention_overrides(
                model_version=MODEL_VERSION,
                network_text=self.network_text,
                merged_cfg=cfg,
                continuation=None,
                root=self.tmp,
                interventions=("hand2_loss",),
            )

    def test_naming_an_intervention_under_legacy_routing_is_refused(self) -> None:
        cfg = self.merged_cfg([f"{name}.istate = FALSE;" for name in LEGACY_INPUTS])
        with (
            mock.patch.object(runner, "INTERVENTION_ROUTING", "legacy"),
            self.assertRaisesRegex(InterventionError, "engine route"),
        ):
            runner._intervention_overrides(
                model_version=MODEL_VERSION,
                network_text=self.network_text,
                merged_cfg=cfg,
                continuation=None,
                root=ROOT,
                interventions=("hand2_loss",),
            )

    def test_the_production_default_is_the_engine(self) -> None:
        self.assertEqual(runner.INTERVENTION_ROUTING, "engine")


if __name__ == "__main__":
    unittest.main()
