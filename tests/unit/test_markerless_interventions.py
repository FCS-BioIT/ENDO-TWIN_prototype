"""O8: an intervention with no legacy marker, statically.

``direct_supported_effect`` rows, their licence, and their composition with the
legacy-backed rows. The runtime gate, including the N+1 invariant, is
``tests/integration/test_markerless_intervention_runtime.py``. The design is
``docs/o8_markerless_interventions.md``.

Every direct row here is synthetic and lives in a sandbox copy of the library;
the committed library holds none.

Since Stage 4b the synthetic rows are v0.6.0 rows: a direct row on a version with
no entity map or expressivity artefact is refused
(``docs/stage4b_direct_admission.md`` §6.6), and v0.5.2 has neither. v0.6.0 has
no legacy markers, so a direct row composes with the *migrated* rows there, and
the cases that needed an active marker are now unreachable for a direct row. The
one mechanical rule that only a marker version can exercise (a target reading an
unrouted legacy input) is still tested on v0.5.2, because it fires before the
admission checks.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import itertools
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.model.runtime import resolve_model
from dt_adoc.perturbations import engine
from dt_adoc.perturbations.engine import (
    ACTIVITY_VETO,
    DIRECT_BASIS,
    LEGACY_BASIS,
    InterventionError,
    intervention_logic_overrides,
    legacy_route_overrides,
    load_intervention_library,
)

_spec = importlib.util.spec_from_file_location(
    "o8_sandbox", ROOT / "tests/fixtures/o8_markerless/sandbox.py"
)
sandbox = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sandbox)

MODEL_VERSION = "adoc-literature-superset-v0.6.0"
V052 = "adoc-literature-superset-v0.5.2"
#: The markers v0.6.0 retired; no rendering may read them.
RETIRED_MARKERS = ("IN_MIFEPRISTONE", "IN_ANTI_SPP1", "IN_HAND2_LOSS")
#: v0.6.0's migrated interventions, the ones a direct row now composes with.
MIGRATED = ("anti_spp1", "hand2_loss", "mifepristone")
X_ROW = (
    (ROOT / "tests/fixtures/o8_markerless/synthetic_compound_x.library.tsv")
    .read_text(encoding="utf-8")
    .rstrip("\n")
)


def _vetoed(overrides: dict[str, str]) -> set[str]:
    return {node for node, logic in overrides.items() if logic.endswith("and not 1")}


class _Sandbox(unittest.TestCase):
    """One sandbox root per test, so an edit never leaks into the next."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = sandbox.build_sandbox(Path(self._tmp.name))
        self.addCleanup(self._tmp.cleanup)

    def append_row(self, row: str) -> None:
        with (self.root / sandbox.LIBRARY).open("a", encoding="utf-8") as handle:
            handle.write(row + "\n")

    def x_row(self, **fields: str) -> str:
        """The synthetic X row with some columns replaced."""
        values = X_ROW.split("\t")
        for name, value in fields.items():
            values[engine.LIBRARY_COLUMNS.index(name)] = value
        return "\t".join(values)

    def load(self):
        return load_intervention_library(self.root)


class DirectRowLicenceTest(_Sandbox):
    """What a direct row must carry, and what it may not name."""

    def test_the_fixture_row_loads_as_a_direct_effect(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_x")
        (effect,) = self.load()["synthetic_compound_x"]
        self.assertEqual(effect.mapping_basis, DIRECT_BASIS)
        self.assertEqual(effect.legacy_input_node, "")
        self.assertEqual(effect.legacy_perturbation_ids, ())
        self.assertEqual(
            (effect.target_node, effect.mode), ("E_GP130_STAT3", ACTIVITY_VETO)
        )

    def test_the_canonical_library_is_unaffected(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_x")
        library = self.load()
        canonical = load_intervention_library(ROOT)
        self.assertEqual({k: library[k] for k in canonical}, canonical)
        for effects in canonical.values():
            self.assertEqual(effects[0].mapping_basis, LEGACY_BASIS)

    def test_a_direct_row_naming_a_legacy_input_is_refused(self) -> None:
        self.append_row(self.x_row(legacy_input_node="IN_XAV939"))
        with self.assertRaisesRegex(InterventionError, "names no legacy input"):
            self.load()

    def test_a_direct_row_naming_a_legacy_perturbation_is_refused(self) -> None:
        self.append_row(self.x_row(legacy_perturbation_ids="mifepristone_after_ht"))
        with self.assertRaisesRegex(InterventionError, "names no legacy input"):
            self.load()

    def test_a_legacy_row_without_a_legacy_input_is_still_refused(self) -> None:
        """The legacy basis cannot be used to skip its own check."""
        self.append_row(self.x_row(mapping_basis=LEGACY_BASIS))
        with self.assertRaises(InterventionError):
            self.load()

    def test_a_direct_row_with_no_executable_effect_is_refused(self) -> None:
        self.append_row(self.x_row(target_node="", mode="no_executable_effect"))
        with self.assertRaisesRegex(InterventionError, "takes mode activity_veto"):
            self.load()

    def test_a_direct_row_under_an_unknown_mode_is_refused(self) -> None:
        self.append_row(self.x_row(mode="activity_force"))
        with self.assertRaisesRegex(InterventionError, "unknown mode"):
            self.load()

    def test_a_direct_row_without_a_target_is_refused(self) -> None:
        self.append_row(self.x_row(target_node=""))
        with self.assertRaises(InterventionError):
            self.load()

    def test_a_nonexistent_target_is_refused(self) -> None:
        self.append_row(self.x_row(target_node="E_NOT_A_NODE"))
        with self.assertRaisesRegex(InterventionError, "not a network node"):
            self.load()

    def test_an_input_target_is_refused(self) -> None:
        for target in ("IN_E2", "IN_HCG", "X_MECHANICAL_STRESS_RELAY"):
            with self.subTest(target=target):
                self.setUp()
                self.append_row(self.x_row(target_node=target))
                with self.assertRaisesRegex(InterventionError, "is an input node"):
                    self.load()

    def test_a_target_with_a_declared_rate_is_refused(self) -> None:
        # The compound first: adding it regenerates the expressivity artefact,
        # whose generator refuses a declared rate on its own (§5.2).
        sandbox.add_compound(self.root, "synthetic_compound_x")
        network = self.root / "models/superset" / MODEL_VERSION / "network.bnd"
        text = network.read_text(encoding="utf-8")
        old = "Node E_GP130_STAT3 {\n  logic = E_LIF;\n"
        self.assertIn(old, text)
        network.write_text(
            text.replace(old, old + "  rate_up = @logic ? 2 : 0;\n"), encoding="utf-8"
        )
        with self.assertRaisesRegex(InterventionError, "declares a rate"):
            self.load()

    def test_a_phenotype_target_is_refused(self) -> None:
        self.append_row(self.x_row(target_node="OUT_MATERNAL_ADHESION_COMPETENCE"))
        with self.assertRaisesRegex(InterventionError, "phenotype node"):
            self.load()

    def test_a_structural_relay_target_is_refused(self) -> None:
        """Every v0.6.0 relay is also a self-loop, so the role is set by hand on a
        node the veto could otherwise mean, to reach the role check itself."""
        sandbox.add_compound(self.root, "synthetic_compound_x")
        dictionary = (
            self.root / "models/superset" / MODEL_VERSION / "node_dictionary.tsv"
        )
        lines = dictionary.read_text(encoding="utf-8").splitlines(keepends=True)
        header = lines[0].rstrip("\n").split("\t")
        role = header.index("model_role")
        for index, line in enumerate(lines):
            fields = line.rstrip("\n").split("\t")
            if fields[0] == "E_GP130_STAT3":
                fields[role] = "structural_uncertainty"
                lines[index] = "\t".join(fields) + "\n"
        dictionary.write_text("".join(lines), encoding="utf-8")
        with self.assertRaisesRegex(InterventionError, "structural_uncertainty node"):
            self.load()

    def test_a_target_reading_an_unrouted_legacy_input_is_refused(self) -> None:
        """Only a marker version has legacy inputs, so this is a v0.5.2 row. The
        mechanical check fires before Stage 4b would refuse the version."""
        network = self.root / "models/superset" / V052 / "network.bnd"
        text = network.read_text(encoding="utf-8")
        old = "  logic = E_LIF;\n"
        network.write_text(
            text.replace(old, "  logic = E_LIF and not IN_ANTI_SPP1;\n", 1),
            encoding="utf-8",
        )
        sandbox.add_compound(self.root, "synthetic_compound_x", ("evidence",))
        self.append_row(self.x_row(model_version=V052))
        with self.assertRaisesRegex(InterventionError, "no legacy row routes"):
            self.load()

    def test_a_target_under_no_dictionary_row_is_refused(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_x")
        dictionary = (
            self.root / "models/superset" / MODEL_VERSION / "node_dictionary.tsv"
        )
        lines = dictionary.read_text(encoding="utf-8").splitlines(keepends=True)
        dictionary.write_text(
            "".join(line for line in lines if not line.startswith("E_GP130_STAT3\t")),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(InterventionError, "no node_dictionary row"):
            self.load()

    def test_missing_evidence_is_refused(self) -> None:
        self.append_row(self.x_row(evidence_ids=""))
        with self.assertRaisesRegex(InterventionError, "carries no provenance"):
            self.load()

    def test_unresolved_evidence_is_refused(self) -> None:
        """The row cites an id the register does not hold: here X's own, with
        its register row left out."""
        self.append_row(X_ROW)
        with self.assertRaisesRegex(InterventionError, "not in context/evidence"):
            self.load()

    def test_a_missing_register_is_refused(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_x")
        (self.root / sandbox.REGISTER).unlink()
        with self.assertRaisesRegex(InterventionError, "need the evidence register"):
            self.load()

    def test_a_missing_abstraction_source_is_refused(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_x")
        (self.root / sandbox.FIXTURE_RELATIVE / "README.md").unlink()
        with self.assertRaisesRegex(InterventionError, "does not exist"):
            self.load()

    def test_missing_sources_or_claim_boundary_are_refused(self) -> None:
        for field in ("abstraction_sources", "model_abstraction", "claim_boundary"):
            with self.subTest(field=field):
                self.setUp()
                sandbox.add_compound(self.root, "synthetic_compound_x")
                self.append_row(self.x_row(**{"intervention_id": "x2", field: ""}))
                with self.assertRaisesRegex(InterventionError, "carries no provenance"):
                    self.load()

    def test_an_unknown_model_version_is_refused(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_x")
        self.append_row(
            self.x_row(intervention_id="x_elsewhere", model_version="no-such-model")
        )
        with self.assertRaisesRegex(InterventionError, "unknown model_version"):
            self.load()

    def test_one_intervention_cannot_mix_bases(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_x")
        self.append_row(
            self.x_row(
                intervention_id="mifepristone",
                intervention_label="Mifepristone",
                intervention_class="protocol_perturbation",
                target_node="E_HBEGF",
            )
        )
        with self.assertRaisesRegex(InterventionError, "intervention-level field"):
            self.load()

    def test_a_target_listed_twice_is_refused(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_x")
        self.append_row(X_ROW)
        with self.assertRaisesRegex(InterventionError, "listed twice"):
            self.load()


class CommittedLibraryTest(unittest.TestCase):
    """Whatever direct rows the committed library holds, none is synthetic.

    The committed library holds no direct row today. Adding a real one is a
    scientific decision, and this test does not pin their number, so adding one
    stays a data change; it only stops the fixture leaking into production.
    """

    def test_no_synthetic_row_or_evidence_is_committed(self) -> None:
        for effects in load_intervention_library(ROOT).values():
            for effect in effects:
                with self.subTest(intervention=effect.intervention_id):
                    self.assertNotEqual(effect.intervention_class, "synthetic_fixture")
                    self.assertFalse(effect.intervention_id.startswith("synthetic_"))
                    for evidence_id in effect.evidence_ids:
                        self.assertFalse(evidence_id.startswith("SYNTHETIC-"))
                    for source in effect.abstraction_sources:
                        self.assertFalse(source.startswith("tests/"))
        register = (ROOT / sandbox.REGISTER).read_text(encoding="utf-8")
        self.assertNotIn("SYNTHETIC-", register)


class _Library(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        root = sandbox.build_sandbox(
            Path(cls._tmp.name), ("synthetic_compound_x", "synthetic_compound_y")
        )
        cls.library = load_intervention_library(root)
        cls.canonical = load_intervention_library(ROOT)
        cls.network_text = resolve_model(MODEL_VERSION, ROOT).network_bnd.read_text(
            encoding="utf-8"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def executed(self, also_active=(), library=None):
        # v0.6.0 has no legacy input, so the route is given none.
        return legacy_route_overrides(
            self.network_text,
            {},
            model_version=MODEL_VERSION,
            library=library or self.library,
            also_active=also_active,
        )

    def documented(self, ids, library=None):
        return intervention_logic_overrides(
            self.network_text,
            list(ids),
            model_version=MODEL_VERSION,
            library=library or self.library,
        )


class DirectExecutionTest(_Library):
    def test_a_direct_row_is_rendered_only_when_named(self) -> None:
        """An unnamed direct row changes the rendering of no combination of the
        migrated interventions. (On v0.5.2 this ranged over the marker values;
        v0.6.0 has none.)"""
        for size in range(len(MIGRATED) + 1):
            for combination in itertools.combinations(MIGRATED, size):
                with self.subTest(combination=combination):
                    self.assertEqual(
                        self.executed(combination),
                        self.executed(combination, library=self.canonical),
                    )

    def test_naming_x_vetoes_exactly_its_target_once(self) -> None:
        quiet = self.executed()
        named = self.executed(("synthetic_compound_x",))
        self.assertEqual(set(named) - set(quiet), {"E_GP130_STAT3"})
        self.assertEqual(named["E_GP130_STAT3"], "(E_LIF) and not 1")
        self.assertEqual({k: v for k, v in named.items() if k in quiet}, quiet)
        self.assertEqual(named["E_GP130_STAT3"].count("and not 1"), 1)

    def test_a_multi_target_direct_compound_vetoes_each_target(self) -> None:
        named = self.executed(("synthetic_compound_y",))
        self.assertEqual(
            _vetoed(named) - _vetoed(self.executed()), {"E_HBEGF", "S_TAZ_ECM"}
        )

    def test_no_rendering_reads_a_marker_for_a_direct_compound(self) -> None:
        named = self.executed(("synthetic_compound_x", "synthetic_compound_y"))
        for node, logic in named.items():
            with self.subTest(node=node):
                self.assertNotRegex(logic, r"\bIN_SYNTHETIC")
                for legacy in RETIRED_MARKERS:
                    self.assertNotRegex(logic, rf"\b{legacy}\b")

    def test_documented_and_executed_composition_agree_on_every_subset(self) -> None:
        """Stage 4a's parity gate, with the direct rows in the library."""
        members = sorted(self.library)
        self.assertIn("synthetic_compound_x", members)
        for size in range(len(members) + 1):
            for combination in itertools.combinations(members, size):
                with self.subTest(combination=combination):
                    self.assertEqual(
                        set(self.documented(combination)),
                        _vetoed(self.executed(combination)),
                    )

    def test_a_direct_and_a_migrated_compound_compose_as_a_union(self) -> None:
        """Before Stage 4b this paired the direct row with a legacy one on
        v0.5.2. A direct row can no longer exist on a marker version, so its
        partner is the migrated row of the same compound."""
        both = self.executed(("mifepristone", "synthetic_compound_x"))
        self.assertEqual(
            _vetoed(both),
            _vetoed(self.executed(("mifepristone",)))
            | _vetoed(self.executed(("synthetic_compound_x",))),
        )
        self.assertEqual(_vetoed(both), {"E_PGR", "S_PGR", "E_GP130_STAT3"})

    def test_a_direct_veto_on_a_migrated_target_is_vetoed_once(self) -> None:
        """A direct row may share a target with a migrated one. Named alongside
        it, the target is vetoed once, as Stage 4a composes two compounds. (The
        v0.5.2 form also set the marker; v0.6.0 has none to set.)"""
        (x,) = self.library["synthetic_compound_x"]
        on_pgr = dataclasses.replace(
            x, intervention_id="direct_pgr", target_node="E_PGR"
        )
        library = {**self.library, "direct_pgr": (on_pgr,)}
        executed = self.executed(("direct_pgr", "mifepristone"), library=library)
        self.assertEqual(executed, self.executed(("mifepristone",), library=library))
        self.assertEqual(executed["E_PGR"].count("and not 1"), 1)

    def test_naming_a_direct_compound_twice_is_refused(self) -> None:
        with self.assertRaisesRegex(InterventionError, "named twice"):
            self.executed(("synthetic_compound_x", "synthetic_compound_x"))

    def test_an_unknown_compound_is_refused(self) -> None:
        with self.assertRaisesRegex(InterventionError, "unknown intervention"):
            self.executed(("synthetic_compound_z",))
        with self.assertRaisesRegex(InterventionError, "unknown intervention"):
            self.executed(("synthetic_compound_x",), library=self.canonical)

    def test_a_bare_string_is_refused(self) -> None:
        with self.assertRaisesRegex(InterventionError, "not one id"):
            self.executed("synthetic_compound_x")

    def test_a_direct_row_never_triggers_the_double_application_refusal(self) -> None:
        """No marker means no "already active" state; only a name applies it,
        alongside every migrated compound too."""
        named = self.executed(("synthetic_compound_x", *MIGRATED))
        self.assertTrue(named["E_GP130_STAT3"].endswith("and not 1"))


class FutureModeConflictTest(_Library):
    """Only the veto exists. These pin that a second mode, once added, cannot
    silently collapse into it or be layered over it on the executed path."""

    def rival(self, target: str, mode: str = "activity_force"):
        (x,) = self.library["synthetic_compound_x"]
        effect = dataclasses.replace(
            x, intervention_id="rival", target_node=target, mode=mode
        )
        return {**self.library, "rival": (effect,)}

    def test_a_mode_conflict_with_a_migrated_compound_is_refused(self) -> None:
        """The v0.5.2 form set the IN_HAND2_LOSS marker; on v0.6.0 the same
        claim on S_HAND2 comes from naming the migrated hand2_loss row."""
        library = self.rival("S_HAND2")
        with (
            mock.patch.object(
                engine, "TARGETED_MODES", (*engine.TARGETED_MODES, "activity_force")
            ),
            self.assertRaisesRegex(InterventionError, "different modes"),
        ):
            self.executed(("hand2_loss", "rival"), library=library)

    def test_a_mode_conflict_between_named_members_is_refused(self) -> None:
        library = self.rival("E_GP130_STAT3")
        with (
            mock.patch.object(
                engine, "TARGETED_MODES", (*engine.TARGETED_MODES, "activity_force")
            ),
            self.assertRaisesRegex(InterventionError, "different modes"),
        ):
            self.executed(("synthetic_compound_x", "rival"), library=library)

    def test_a_supported_mode_without_a_renderer_is_refused(self) -> None:
        library = self.rival("E_GP130_STAT3")
        with mock.patch.object(
            engine, "TARGETED_MODES", (*engine.TARGETED_MODES, "activity_force")
        ):
            with self.assertRaisesRegex(InterventionError, "no rendering for mode"):
                self.executed(("rival",), library=library)
            with self.assertRaisesRegex(InterventionError, "no rendering for mode"):
                self.documented(("rival",), library=library)


if __name__ == "__main__":
    unittest.main()
