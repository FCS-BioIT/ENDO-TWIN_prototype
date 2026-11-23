"""The perturbation spec selects existing mechanisms and refuses everything else."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.perturbations.spec import (
    INPUT_CHANGE,
    REGISTERED_INTERVENTION,
    PerturbationSpecError,
    effect_provenance,
    input_nodes,
    load_spec,
    parse_spec,
    validate_spec,
)

MV = "adoc-literature-superset-v0.6.0"


def spec(**kw):
    payload = {"name": "t", "model_version": MV, "start": "hormone_treated_maternal"}
    payload.update(kw)
    return parse_spec(payload)


class ParseTests(unittest.TestCase):
    def test_reserved_keys_are_refused_by_name(self):
        for key in (
            "effects",
            "veto",
            "hypothetical_vetoes",
            "force_on",
            "rule_replace",
        ):
            with (
                self.subTest(key=key),
                self.assertRaisesRegex(PerturbationSpecError, key),
            ):
                spec(**{key: ["E_GP130_STAT3"]})

    def test_unknown_key_is_refused(self):
        with self.assertRaisesRegex(PerturbationSpecError, "unknown keys"):
            spec(dose=3)

    def test_values_must_be_boolean(self):
        with self.assertRaises(PerturbationSpecError):
            spec(input_changes={"IN_PROGESTIN": "off"})
        self.assertEqual(
            spec(input_changes={"IN_PROGESTIN": 0}).input_changes,
            {"IN_PROGESTIN": False},
        )

    def test_interventions_is_a_list(self):
        with self.assertRaises(PerturbationSpecError):
            spec(interventions="mifepristone")

    def test_yaml_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "s.yaml"
            path.write_text(
                "schema: dt_adoc.perturbation_spec/1\nname: pw\n"
                f"model_version: {MV}\nstart: hormone_treated_maternal\n"
                "input_changes:\n  IN_PROGESTIN: false\n"
            )
            s = load_spec(path)
        self.assertEqual(s.to_dict()["input_changes"], {"IN_PROGESTIN": False})


class ValidateTests(unittest.TestCase):
    def test_input_nodes_are_self_rules(self):
        nodes = input_nodes(MV)
        self.assertIn("IN_PROGESTIN", nodes)
        self.assertNotIn("E_PGR", nodes)
        self.assertTrue(all(n.startswith("IN_") for n in nodes))

    def test_progestin_withdrawal_is_valid(self):
        validate_spec(spec(input_changes={"IN_PROGESTIN": False}))

    def test_a_non_input_node_cannot_be_set(self):
        with self.assertRaisesRegex(PerturbationSpecError, "not a declared input"):
            validate_spec(spec(input_changes={"E_GP130_STAT3": False}))
        with self.assertRaisesRegex(PerturbationSpecError, "not a declared input"):
            validate_spec(spec(input_changes={"X_INTERFACE_SPP1_RELAY": False}))

    def test_an_input_the_start_step_does_not_declare_is_refused(self):
        # v0.5.1 hormone_treated_maternal does not declare IN_HAND2_LOSS, which
        # starts OFF; OFF -> OFF would be published as a perturbation.
        s = parse_spec(
            {
                "name": "t",
                "model_version": "adoc-literature-superset-v0.5.1",
                "start": "hormone_treated_maternal",
                "input_changes": {"IN_HAND2_LOSS": False},
            }
        )
        with self.assertRaisesRegex(
            PerturbationSpecError, "not declared by the last step"
        ):
            validate_spec(s)

    def test_every_accepted_change_records_a_known_starting_value(self):
        s = spec(input_changes={"IN_PROGESTIN": False})
        validate_spec(s)
        rec = effect_provenance(s)[0]
        self.assertIs(rec["from"], True)
        self.assertNotEqual(rec["from"], rec["to"])

    def test_a_change_that_changes_nothing_is_refused(self):
        with self.assertRaisesRegex(PerturbationSpecError, "change nothing"):
            validate_spec(spec(input_changes={"IN_PROGESTIN": True}))

    def test_an_empty_spec_is_refused(self):
        with self.assertRaisesRegex(PerturbationSpecError, "no effect"):
            validate_spec(spec())

    def test_unregistered_intervention_is_refused(self):
        with self.assertRaisesRegex(PerturbationSpecError, "no library row"):
            validate_spec(spec(interventions=["stat3_inhibitor"]))

    def test_intervention_already_active_in_start_is_refused(self):
        s = spec(start="hormone_treated_mifepristone", interventions=["mifepristone"])
        with self.assertRaisesRegex(PerturbationSpecError, "already active"):
            validate_spec(s)

    def test_unknown_rule_variant_is_refused(self):
        with self.assertRaises(PerturbationSpecError):
            validate_spec(spec(rule_variants={"no_such_family": "x"}))

    def test_provenance_classes_are_machine_readable(self):
        s = spec(input_changes={"IN_PROGESTIN": False}, interventions=["mifepristone"])
        validate_spec(s)
        rec = effect_provenance(s)
        self.assertEqual(
            [r["provenance_class"] for r in rec],
            [INPUT_CHANGE, REGISTERED_INTERVENTION],
        )
        self.assertEqual(rec[0]["from"], True)
        targets = {e["target_node"] for e in rec[1]["effects"]}
        self.assertEqual(targets, {"E_PGR", "S_PGR"})
        self.assertTrue(all(e["mapping_basis"] for e in rec[1]["effects"]))

    def test_committed_specs_validate(self):
        paths = sorted((ROOT / "context" / "perturbations").glob("*.yaml"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(spec=path.name):
                validate_spec(load_spec(path))

    def test_control_has_no_effects(self):
        self.assertTrue(spec(input_changes={"IN_PROGESTIN": False}).control().is_empty)


if __name__ == "__main__":
    unittest.main()
