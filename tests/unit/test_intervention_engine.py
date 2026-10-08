"""Stage 1 of the intervention-layer refactor: library and rendering, statically.

Gates G1-G4 of ``docs/intervention_layer_refactor_plan.md``. The same-seed
MaBoSS gates (G5, G6) are in
``tests/integration/test_intervention_engine_runtime.py``.
"""

from __future__ import annotations

import dataclasses
import itertools
import json
import re
import shutil
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
from dt_adoc.perturbations import engine
from dt_adoc.perturbations.engine import (
    ACTIVITY_VETO,
    LEGACY_BASIS,
    LIBRARY_PATH,
    NO_EXECUTABLE_EFFECT,
    InterventionError,
    intervention_logic_overrides,
    library_for_version,
    load_intervention_library,
    render_interventions,
)

MODEL_VERSION = "adoc-literature-superset-v0.5.2"
KEYWORDS = {"and", "or", "not"}
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _rules(network_text: str) -> dict[str, str]:
    rules = {}
    for match in NODE_BLOCK_RE.finditer(network_text):
        (logic_match,) = LOGIC_LINE_RE.finditer(match.group(3))
        rules[match.group(2)] = logic_match.group(2).strip()
    return rules


def _variables(logic: str) -> set[str]:
    return {token for token in IDENTIFIER.findall(logic) if token not in KEYWORDS}


def _evaluate(logic: str, assignment: dict[str, bool]) -> bool:
    return bool(eval(logic, {"__builtins__": {}}, dict(assignment)))


class _Fixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # G1-G4 are the gates of the legacy-backed rows. A direct row has no
        # legacy input to resolve and is gated in test_markerless_interventions,
        # so adding one to the library changes nothing these tests assert.
        # Stage 3 adds v0.6.0 rows under the same ids; these gates are v0.5.2's.
        cls.library = {
            key: effects
            for key, effects in library_for_version(
                load_intervention_library(ROOT), MODEL_VERSION
            ).items()
            if effects[0].mapping_basis == LEGACY_BASIS
        }
        cls.network_text = resolve_model(MODEL_VERSION, ROOT).network_bnd.read_text(
            encoding="utf-8"
        )
        cls.rules = _rules(cls.network_text)
        cls.vetoing = {
            key: effects
            for key, effects in cls.library.items()
            if effects[0].mode == ACTIVITY_VETO
        }

    def render(self, intervention_id: str) -> str:
        return render_interventions(
            self.network_text,
            [intervention_id],
            model_version=MODEL_VERSION,
            library=self.library,
        )


class LibraryResolutionTest(_Fixture):
    """G1: every row resolves, and the library adds and omits no target."""

    def test_the_library_holds_exactly_the_v052_intervention_inputs(self) -> None:
        self.assertEqual(
            {
                key: effects[0].legacy_input_node
                for key, effects in self.library.items()
            },
            {
                "mifepristone": "IN_MIFEPRISTONE",
                "anti_spp1": "IN_ANTI_SPP1",
                "hand2_loss": "IN_HAND2_LOSS",
                "xav939": "IN_XAV939",
            },
        )
        for effects in self.library.values():
            for effect in effects:
                self.assertEqual(effect.model_version, MODEL_VERSION)
                self.assertEqual(effect.mapping_basis, "executable_legacy_behaviour")

    def test_each_legacy_input_is_a_free_input_of_the_model(self) -> None:
        for effects in self.library.values():
            legacy = effects[0].legacy_input_node
            self.assertEqual(self.rules.get(legacy), legacy)

    def test_targets_are_exactly_the_rules_that_read_the_legacy_input(self) -> None:
        """Derived from the .bnd, so a new reader or a dropped target fails here."""
        for key, effects in self.library.items():
            legacy = effects[0].legacy_input_node
            readers = {
                node
                for node, logic in self.rules.items()
                if node != legacy and legacy in _variables(logic)
            }
            targets = {e.target_node for e in effects if e.mode == ACTIVITY_VETO}
            self.assertEqual(targets, readers, key)

    def test_targets_are_biological_nodes_not_inputs(self) -> None:
        for effects in self.vetoing.values():
            for effect in effects:
                self.assertIn(effect.target_node, self.rules)
                self.assertNotEqual(self.rules[effect.target_node], effect.target_node)
                self.assertFalse(effect.target_node.startswith("IN_"))

    def test_mifepristone_vetoes_both_pgr_activity_nodes(self) -> None:
        self.assertEqual(
            sorted(e.target_node for e in self.library["mifepristone"]),
            ["E_PGR", "S_PGR"],
        )

    def test_anti_spp1_vetoes_only_the_free_luminal_pool(self) -> None:
        self.assertEqual(
            [e.target_node for e in self.library["anti_spp1"]], ["X_SPP1_LUMEN_FREE"]
        )
        rendered = _rules(self.render("anti_spp1"))
        for expression_node in ("E_SPP1_EXPR", "S_SPP1"):
            self.assertEqual(rendered[expression_node], self.rules[expression_node])

    def test_hand2_loss_vetoes_stromal_hand2(self) -> None:
        self.assertEqual(
            [e.target_node for e in self.library["hand2_loss"]], ["S_HAND2"]
        )

    def test_xav939_inertness_is_recorded_as_executable_only(self) -> None:
        """The model encodes no effect; the row must not read as a biological claim."""
        (effect,) = self.library["xav939"]
        self.assertEqual(effect.mode, NO_EXECUTABLE_EFFECT)
        self.assertEqual(effect.target_node, "")
        self.assertEqual(self.render("xav939"), self.network_text)
        self.assertIn(
            "not a claim that XAV939 has no biological effect", effect.claim_boundary
        )

    def test_rows_agree_with_the_declared_perturbations(self) -> None:
        declared = json.loads(
            (ROOT / "config/perturbations.yaml").read_text(encoding="utf-8")
        )
        by_id = {p["perturbation_id"]: p for p in declared["perturbations"]}
        listed: set[str] = set()
        for effects in self.library.values():
            for perturbation_id in effects[0].legacy_perturbation_ids:
                self.assertEqual(
                    by_id[perturbation_id]["target_node"], effects[0].legacy_input_node
                )
                listed.add(perturbation_id)
        legacy_inputs = {
            effects[0].legacy_input_node for effects in self.library.values()
        }
        expected = {k for k, p in by_id.items() if p["target_node"] in legacy_inputs}
        self.assertEqual(listed, expected)

    def test_every_row_carries_provenance(self) -> None:
        for effects in self.library.values():
            for effect in effects:
                self.assertTrue(effect.evidence_ids)
                self.assertTrue(effect.model_abstraction)
                for source in effect.abstraction_sources:
                    self.assertTrue((ROOT / source.split("#")[0]).is_file(), source)


class RuleEquivalenceTest(_Fixture):
    """G2: the rendered veto with the input at 0 is the legacy rule with it at 1."""

    def test_vetoed_rules_are_exhaustively_equivalent(self) -> None:
        for key, effects in self.vetoing.items():
            legacy = effects[0].legacy_input_node
            rendered = _rules(self.render(key))
            for effect in effects:
                old = self.rules[effect.target_node]
                new = rendered[effect.target_node]
                names = sorted(_variables(old) | _variables(new))
                self.assertIn(legacy, names)
                for values in itertools.product((False, True), repeat=len(names)):
                    point = dict(zip(names, values))
                    with_input = {**point, legacy: True}
                    without_input = {**point, legacy: False}
                    self.assertEqual(
                        _evaluate(new, without_input), _evaluate(old, with_input), key
                    )
                    self.assertFalse(_evaluate(new, point), key)

    def test_no_intervention_renders_the_identity(self) -> None:
        self.assertEqual(
            render_interventions(
                self.network_text, [], model_version=MODEL_VERSION, library=self.library
            ),
            self.network_text,
        )


class LocalityTest(_Fixture):
    """G3: only the targets' logic lines change, and no kinetics appear."""

    def test_only_target_logic_lines_change(self) -> None:
        old_lines = self.network_text.splitlines()
        for key, effects in self.vetoing.items():
            new_lines = self.render(key).splitlines()
            self.assertEqual(len(new_lines), len(old_lines))
            changed = [
                i for i, (a, b) in enumerate(zip(old_lines, new_lines)) if a != b
            ]
            self.assertEqual(len(changed), len(effects), key)
            targets = {e.target_node for e in effects}
            for index in changed:
                self.assertRegex(new_lines[index], r"^\s*logic = \(.+\) and not 1;$")
                header = next(
                    line
                    for line in reversed(old_lines[:index])
                    if line.startswith("Node ")
                )
                self.assertIn(header.split()[1], targets)

    def test_no_rate_lines_exist_or_are_introduced(self) -> None:
        rate = re.compile(r"(?m)^\s*(rate_up|rate_down|max_rate)\b")
        self.assertIsNone(rate.search(self.network_text))
        for key in self.library:
            self.assertIsNone(rate.search(self.render(key)), key)

    def test_overrides_and_rendering_agree(self) -> None:
        for key in self.vetoing:
            overrides = intervention_logic_overrides(
                self.network_text,
                [key],
                model_version=MODEL_VERSION,
                library=self.library,
            )
            self.assertEqual(_rules(self.render(key)), {**self.rules, **overrides})


class RefusalTest(_Fixture):
    """G4: requests Stage 1 does not support are refused, not approximated."""

    def assertRefused(
        self, ids: list[str], *, library=None, text=None, version=MODEL_VERSION
    ):
        with self.assertRaises(InterventionError):
            render_interventions(
                text if text is not None else self.network_text,
                ids,
                model_version=version,
                library=library if library is not None else self.library,
            )

    def test_unknown_intervention(self) -> None:
        self.assertRefused(["not_a_compound"])

    def test_model_version_mismatch(self) -> None:
        self.assertRefused(["mifepristone"], version="adoc-core-v0.1.0")

    def test_an_intervention_named_twice(self) -> None:
        self.assertRefused(["mifepristone", "mifepristone"])

    def test_an_input_as_target(self) -> None:
        (effect,) = self.library["hand2_loss"]
        bad = {"hand2_loss": (dataclasses.replace(effect, target_node="IN_E2"),)}
        self.assertRefused(["hand2_loss"], library=bad)

    def test_a_missing_target(self) -> None:
        (effect,) = self.library["hand2_loss"]
        bad = {"hand2_loss": (dataclasses.replace(effect, target_node="S_NOT_A_NODE"),)}
        self.assertRefused(["hand2_loss"], library=bad)

    def test_a_target_with_a_declared_rate(self) -> None:
        text = self.network_text.replace(
            "Node S_HAND2 {\n", "Node S_HAND2 {\n  rate_down = 5;\n", 1
        )
        self.assertNotEqual(text, self.network_text)
        self.assertRefused(["hand2_loss"], text=text)

    def test_a_rate_on_the_logic_line(self) -> None:
        text = self.network_text.replace(
            "  logic = (S_BMP2 or S_PGR) and not IN_HAND2_LOSS;",
            "  logic = (S_BMP2 or S_PGR) and not IN_HAND2_LOSS; rate_down = 5;",
            1,
        )
        self.assertNotEqual(text, self.network_text)
        self.assertRefused(["hand2_loss"], text=text)

    def test_a_declared_max_rate(self) -> None:
        text = self.network_text.replace(
            "Node S_HAND2 {\n", "Node S_HAND2 {\n  max_rate = 5;\n", 1
        )
        self.assertNotEqual(text, self.network_text)
        self.assertRefused(["hand2_loss"], text=text)

    def test_a_parenthesised_input_as_target(self) -> None:
        text = self.network_text.replace("  logic = IN_E2;", "  logic = (IN_E2);", 1)
        self.assertNotEqual(text, self.network_text)
        (effect,) = self.library["hand2_loss"]
        bad = {"hand2_loss": (dataclasses.replace(effect, target_node="IN_E2"),)}
        self.assertRefused(["hand2_loss"], library=bad, text=text)

    def test_a_single_id_string(self) -> None:
        with self.assertRaisesRegex(InterventionError, "not one id"):
            render_interventions(
                self.network_text,
                "hand2_loss",
                model_version=MODEL_VERSION,
                library=self.library,
            )


class CompositionTest(_Fixture):
    """Stage 4a: several interventions compose as the union of their effects.

    Stage 1 refused more than one. That was a scope guard while no composition
    rule was tested, not a statement about the model, and Stage 4a replaces it
    with the rule documented in ``intervention_logic_overrides``.
    """

    def render_many(self, ids: list[str]) -> dict[str, str]:
        return intervention_logic_overrides(
            self.network_text,
            ids,
            model_version=MODEL_VERSION,
            library=self.library,
        )

    def test_a_combination_is_the_union_of_its_members(self) -> None:
        members = ["mifepristone", "anti_spp1", "hand2_loss"]
        combined = self.render_many(members)
        union: dict[str, str] = {}
        for member in members:
            union.update(self.render_many([member]))
        self.assertEqual(combined, union)
        self.assertEqual(
            sorted(combined), ["E_PGR", "S_HAND2", "S_PGR", "X_SPP1_LUMEN_FREE"]
        )

    def test_a_multi_target_compound_vetoes_each_target(self) -> None:
        """Polypharmacology needs no combination: mifepristone is already two
        targets in one library entry."""
        rendered = self.render_many(["mifepristone"])
        self.assertEqual(sorted(rendered), ["E_PGR", "S_PGR"])
        for logic in rendered.values():
            self.assertTrue(logic.endswith("and not 1"))

    def test_order_does_not_matter(self) -> None:
        self.assertEqual(
            self.render_many(["mifepristone", "anti_spp1"]),
            self.render_many(["anti_spp1", "mifepristone"]),
        )

    def test_an_inert_member_contributes_nothing(self) -> None:
        self.assertEqual(
            self.render_many(["anti_spp1", "xav939"]), self.render_many(["anti_spp1"])
        )

    def test_a_shared_target_is_vetoed_once(self) -> None:
        """Two interventions on one target leave one veto: the veto is already
        false everywhere, so a second cannot make it more false."""
        (effect,) = self.library["hand2_loss"]
        twin = dataclasses.replace(
            effect, intervention_id="hand2_loss_twin", legacy_input_node="IN_TWIN"
        )
        library = {**self.library, "hand2_loss_twin": (twin,)}
        both = intervention_logic_overrides(
            self.network_text,
            ["hand2_loss", "hand2_loss_twin"],
            model_version=MODEL_VERSION,
            library=library,
        )
        self.assertEqual(both, self.render_many(["hand2_loss"]))

    def test_two_modes_on_one_target_are_refused(self) -> None:
        """No second mode exists yet, so this guards the future rather than the
        present: a conflict must never be resolved by whichever row came last."""
        (effect,) = self.library["hand2_loss"]
        rival = dataclasses.replace(
            effect,
            intervention_id="hand2_forced_on",
            legacy_input_node="IN_RIVAL",
            mode="activity_force",
        )
        library = {**self.library, "hand2_forced_on": (rival,)}
        # The mode has to be supported for the conflict to be the live question;
        # an unsupported one is refused first, which the next test pins.
        with (
            mock.patch.object(
                engine, "TARGETED_MODES", (*engine.TARGETED_MODES, "activity_force")
            ),
            self.assertRaisesRegex(InterventionError, "different modes"),
        ):
            intervention_logic_overrides(
                self.network_text,
                ["hand2_loss", "hand2_forced_on"],
                model_version=MODEL_VERSION,
                library=library,
            )

    def test_an_unsupported_mode_is_refused_rather_than_vetoed(self) -> None:
        """A mode this engine does not implement must not be rendered as a veto,
        which would silently give it the one behaviour that exists."""
        (effect,) = self.library["hand2_loss"]
        exotic = dataclasses.replace(effect, mode="activity_force")
        library = {**self.library, "hand2_loss": (exotic,)}
        with self.assertRaisesRegex(InterventionError, "unsupported mode"):
            intervention_logic_overrides(
                self.network_text,
                ["hand2_loss"],
                model_version=MODEL_VERSION,
                library=library,
            )

    def test_a_combination_with_an_unknown_member_is_refused(self) -> None:
        with self.assertRaises(InterventionError):
            self.render_many(["mifepristone", "not_a_compound"])


class LibraryValidationTest(unittest.TestCase):
    """The loader refuses malformed rows instead of rendering something partial."""

    def _load_with(self, edit) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # The models too: a migrated row's licence reads its model and parent.
            shutil.copytree(ROOT / "models", Path(tmp) / "models")
            target = Path(tmp) / LIBRARY_PATH
            target.parent.mkdir(parents=True)
            shutil.copy(ROOT / LIBRARY_PATH, target)
            target.write_text(
                edit(target.read_text(encoding="utf-8")), encoding="utf-8"
            )
            load_intervention_library(Path(tmp))

    def test_the_committed_library_loads(self) -> None:
        self._load_with(lambda text: text)

    def test_unknown_mode(self) -> None:
        with self.assertRaises(InterventionError):
            self._load_with(
                lambda t: t.replace("\tactivity_veto\t", "\tfast_clamp\t", 1)
            )

    def test_target_on_a_no_effect_row(self) -> None:
        with self.assertRaises(InterventionError):
            self._load_with(
                lambda t: t.replace(
                    "\t\tno_executable_effect", "\tE_PGR\tno_executable_effect"
                )
            )

    def test_duplicate_target(self) -> None:
        def duplicate(text: str) -> str:
            lines = text.splitlines(keepends=True)
            return "".join(lines + [lines[1]])

        with self.assertRaises(InterventionError):
            self._load_with(duplicate)

    def test_ragged_row(self) -> None:
        with self.assertRaises(InterventionError):
            self._load_with(lambda t: t + "orphan\tvalue\n")

    def test_rows_of_one_intervention_disagree(self) -> None:
        with self.assertRaises(InterventionError):
            self._load_with(
                lambda t: t.replace("Mifepristone\t", "Mifepristone (alt)\t", 1)
            )

    def test_unknown_mapping_basis(self) -> None:
        with self.assertRaises(InterventionError):
            self._load_with(
                lambda t: t.replace(
                    "executable_legacy_behaviour", "literature_claim", 1
                )
            )

    def test_a_veto_row_without_a_declared_perturbation(self) -> None:
        with self.assertRaises(InterventionError):
            self._load_with(lambda t: t.replace("\thand2_loss_after_ht\t", "\t\t", 1))

    def test_missing_provenance(self) -> None:
        with self.assertRaises(InterventionError):
            self._load_with(lambda t: t.replace("\tSOFIA-HT-001\t", "\t\t", 1))


if __name__ == "__main__":
    unittest.main()
