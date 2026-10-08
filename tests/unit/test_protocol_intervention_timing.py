"""Static gates for step-level intervention timing (no MaBoSS run).

See ``docs/protocol_intervention_timing.md``. The runtime gates are in
``tests/integration/test_protocol_intervention_timing_runtime.py``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.model.catalog import load_protocols
from dt_adoc.perturbations.engine import InterventionError, load_intervention_library
from dt_adoc.protocols.conditions import (
    markerless_protocol_rows,
    protocol_definitions,
    step_interventions,
)
from dt_adoc.protocols.runner import protocol_sequence
from dt_adoc.protocols.schema import ProtocolStep
from dt_adoc.simulation import runner

_spec = importlib.util.spec_from_file_location(
    "protocol_timing_sandbox", ROOT / "tests/fixtures/protocol_timing/sandbox.py"
)
sandbox = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sandbox)

MODEL_VERSION = sandbox.MODEL_VERSION
LIBRARY = load_intervention_library(ROOT)


def _parse(raw, *, model_version=MODEL_VERSION, input_states=None, library=LIBRARY):
    return step_interventions(
        raw,
        protocol_id="p",
        step_id="s",
        model_version=model_version,
        input_states=input_states or {},
        library=library,
    )


def _model_versions() -> list[str]:
    declared = {row["model_version"] for row in load_protocols(ROOT)["protocols"]}
    supersets = {path.name for path in (ROOT / "models/superset").glob("adoc-*")}
    return sorted(declared | supersets)


class StepFieldTest(unittest.TestCase):
    def test_absent_and_empty_both_mean_none(self) -> None:
        self.assertEqual(_parse(None), ())
        self.assertEqual(_parse([]), ())
        self.assertEqual(ProtocolStep("s", 1, 1.0, "", {}).interventions, ())

    def test_order_is_canonicalised(self) -> None:
        self.assertEqual(
            _parse(["mifepristone", "anti_spp1"]), _parse(["anti_spp1", "mifepristone"])
        )
        self.assertEqual(
            _parse(["mifepristone", "anti_spp1"]), ("anti_spp1", "mifepristone")
        )

    def test_refusals(self) -> None:
        cases = {
            "a string": ("mifepristone", {}, "a list of intervention ids"),
            "a non-string member": ([1], {}, "a list of intervention ids"),
            "an empty id": ([""], {}, "a list of intervention ids"),
            "a duplicate": (["anti_spp1", "anti_spp1"], {}, "named twice"),
            "an unknown id": (["compound_z"], {}, "unknown intervention"),
            "marker and name": (
                ["mifepristone"],
                {"IN_MIFEPRISTONE": True},
                "declare its timing one way",
            ),
        }
        for label, (raw, inputs, message) in cases.items():
            with (
                self.subTest(label),
                self.assertRaisesRegex(InterventionError, message),
            ):
                _parse(raw, input_states=inputs)

    def test_a_marker_set_off_does_not_conflict(self) -> None:
        self.assertEqual(
            _parse(["mifepristone"], input_states={"IN_MIFEPRISTONE": False}),
            ("mifepristone",),
        )

    def test_a_wrong_model_mapping_is_refused(self) -> None:
        with self.assertRaisesRegex(InterventionError, "is defined for"):
            _parse(["hand2_loss"], model_version="adoc-literature-superset-v0.5.1")

    def test_no_library_refuses_a_name_but_not_an_empty_list(self) -> None:
        self.assertEqual(_parse([], library=None), ())
        with self.assertRaisesRegex(InterventionError, "no intervention library"):
            _parse(["mifepristone"], library=None)

    def test_a_markerless_direct_intervention_is_legal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = sandbox.o8_sandbox.build_sandbox(
                Path(tmp), ("synthetic_compound_x",)
            )
            library = load_intervention_library(root)
        # A direct compound runs on v0.6.0 only, since Stage 4b.
        self.assertEqual(
            _parse(
                ["synthetic_compound_x"],
                model_version=sandbox.MARKERLESS_VERSION,
                library=library,
            ),
            ("synthetic_compound_x",),
        )


class CanonicalProtocolsUnchangedTest(unittest.TestCase):
    """O8a migrated no committed protocol.

    Stage 3 later migrated v0.6.0's, in a file of their own
    (``config/protocols_markerless.yaml``, ``docs/intervention_layer_stage3.md``),
    so the marker-timed versions below are every version that file does not
    serve; ``tests/unit/test_v060_marker_removal.py`` guards the migrated ones.
    """

    def test_no_committed_protocol_declares_the_field(self) -> None:
        for row in load_protocols(ROOT)["protocols"]:
            for step in row["steps"]:
                self.assertNotIn("interventions", step, row["protocol_id"])

    def test_every_model_version_resolves_with_no_named_timing(self) -> None:
        markerless = {row["model_version"] for row in markerless_protocol_rows(ROOT)}
        self.assertEqual(markerless, {"adoc-literature-superset-v0.6.0"})
        for model_version in sorted(set(_model_versions()) - markerless):
            with self.subTest(model_version=model_version):
                definitions = protocol_definitions(ROOT, model_version=model_version)
                self.assertTrue(definitions)
                for definition in definitions.values():
                    for step in definition.steps:
                        self.assertEqual(step.interventions, ())
                    for row in protocol_sequence(
                        definition.protocol_id, ROOT, model_version=model_version
                    ):
                        self.assertNotIn("interventions", row)


class ProtocolFileValidationTest(unittest.TestCase):
    """The parser refuses a bad step when ``protocol_definitions`` loads it."""

    def _definitions(self, interventions, inputs=None):
        base = sandbox.canonical_rows()["hormone_treated_anti_spp1"]
        variant = sandbox.renamed(
            base,
            "variant",
            steps=[
                sandbox.step(
                    base["steps"][0],
                    "s",
                    1,
                    inputs=inputs or {"IN_ANTI_SPP1": False},
                    interventions=interventions,
                )
            ],
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = sandbox.build_sandbox(Path(tmp), [variant])
            return protocol_definitions(root, model_version=MODEL_VERSION)

    def test_a_valid_step_loads(self) -> None:
        definitions = self._definitions(["mifepristone", "anti_spp1"])
        self.assertEqual(
            definitions["variant"].steps[0].interventions, ("anti_spp1", "mifepristone")
        )

    def test_bad_steps_are_refused_at_load(self) -> None:
        cases = {
            "duplicate": (["anti_spp1", "anti_spp1"], None, "named twice"),
            "unknown": (["compound_z"], None, "unknown intervention"),
            "double": (["anti_spp1"], {"IN_ANTI_SPP1": True}, "one way, not both"),
        }
        for label, (names, inputs, message) in cases.items():
            with (
                self.subTest(label),
                self.assertRaisesRegex(InterventionError, message),
            ):
                self._definitions(names, inputs)

    def test_a_wrong_model_row_is_refused_at_load(self) -> None:
        base = sandbox.canonical_rows()["hormone_treated_anti_spp1"]
        with tempfile.TemporaryDirectory() as tmp:
            root = sandbox.o8_sandbox.build_sandbox(Path(tmp))
            path = root / sandbox.PROTOCOLS
            payload = json.loads(path.read_text(encoding="utf-8"))
            row = sandbox.renamed(
                base,
                "variant",
                steps=[
                    sandbox.step(base["steps"][0], "s", 1, interventions=["anti_spp1"])
                ],
            )
            row["model_version"] = "adoc-literature-superset-v0.5.1"
            row["steps"][0]["input_states"]["IN_ANTI_SPP1"] = False
            payload["protocols"].append(row)
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(InterventionError, "is defined for"):
                protocol_definitions(
                    root, model_version="adoc-literature-superset-v0.5.1"
                )


class MergedCfgLifecycleTest(unittest.TestCase):
    """The holder of a result owns its merged-cfg directory and releases it."""

    def _result(self) -> runner.ConditionRunResult:
        directory = Path(tempfile.mkdtemp(prefix="dt_adoc_cfg_"))
        cfg = directory / "x.cfg"
        cfg.write_text("x", encoding="utf-8")
        return runner.ConditionRunResult(
            merged_cfg=cfg,
            raw_result=None,
            last_nodes_probtraj=None,
            last_states_probtraj=None,
            last={},
        )

    def test_release_removes_every_step_directory_and_is_idempotent(self) -> None:
        steps = (self._result(), self._result())
        run = runner.ProtocolRunResult("p", steps, (None, None), None, False)
        run.release()
        run.release()
        for step in steps:
            self.assertFalse(step.merged_cfg.parent.exists())

    def test_a_with_block_releases_on_exit_and_on_error(self) -> None:
        for raises in (False, True):
            step = self._result()
            run = runner.ProtocolRunResult("p", (step,), (None,), None, False)
            with self.subTest(raises=raises):
                try:
                    with run as held:
                        self.assertTrue(held.final_result.merged_cfg.is_file())
                        if raises:
                            raise RuntimeError
                except RuntimeError:
                    pass
                self.assertFalse(step.merged_cfg.parent.exists())


if __name__ == "__main__":
    unittest.main()
