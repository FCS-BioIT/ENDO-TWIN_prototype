"""U6 -- node semantics, the component combinator, and the component map.

What these tests hold, in the order `docs/v05_mechanistic_integration_plan.md`
§17 lists U6's deliverables:

* the three semantic axes for all 59 nodes, as a generated view that agrees with
  the frozen `node_rna_interpretability.tsv` on every node it covers and leaves
  the evidence-root observation map byte-identical;
* the four-state enum and its mapping from the frozen support vocabulary, which
  keeps "integrity control FAILED" and "no integrity control DEFINED" apart;
* §6.3's combination table, proven by exhaustive enumeration against an
  independent statement of it (T-D), with empty groups raising;
* `provisional_corrected_layer_only` as orthogonal metadata with dual AND/OR
  propagation, and the clamp veto (T-E2);
* the component map's schema, including the declared-group path that no
  committed row uses yet, `undeclared` as a valid inert state (T-J), and the
  owner's HGNC decision for `CTGF`/`CYR61` (T-E).
"""

from __future__ import annotations

import ast
import csv
import inspect
import io
import itertools
import subprocess
import unittest
from pathlib import Path

from dt_adoc.scrna import components as K
from dt_adoc.scrna.components import (
    AND,
    OR,
    ComponentMapError,
    Evidence,
    EvidenceState,
    Group,
)

ROOT = Path(__file__).resolve().parents[2]
S = EvidenceState
EVIDENCE_ROOT = "91f79ed"


def _tsv(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text), delimiter="\t"))


def _git(*args: str) -> subprocess.CompletedProcess[bytes] | None:
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, check=False
        )
    except OSError:
        return None


def _evidence_root_unavailable() -> str:
    """Why the evidence-root blobs cannot be read here, or "" if they can.

    Two different situations, reported as such. Outside this repository's own
    work tree (no git, or a bundle unpacked inside some other checkout) there is
    nothing to compare against. Inside it, the commit can still be missing -- a
    shallow clone or a synthetic review snapshot -- and no test in this
    repository requires full history, so that is a skip too, named for what it
    is. A reachable commit whose blob is missing is neither: it fails.
    """
    top = _git("rev-parse", "--show-toplevel")
    if top is None or top.returncode:
        return "not a git work tree (git unavailable or ROOT outside any repository)"
    if Path(top.stdout.decode().strip()).resolve() != ROOT.resolve():
        return "ROOT is not the top of its own git work tree"
    commit = _git("cat-file", "-e", f"{EVIDENCE_ROOT}^{{commit}}")
    if commit is None or commit.returncode:
        return (
            f"evidence-root commit {EVIDENCE_ROOT} is not available in this clone "
            "(shallow history or a synthetic snapshot); blob identity unchecked"
        )
    return ""


class GeneratedArtifactsDoNotDrift(unittest.TestCase):
    def test_both_artifacts_regenerate_byte_for_byte(self) -> None:
        from dt_adoc.scrna.observability import SEMANTICS, render_semantics

        self.assertEqual(
            (ROOT / SEMANTICS).read_text(encoding="utf-8"), render_semantics(ROOT)
        )
        self.assertEqual(
            (ROOT / K.COMPONENT_MAP).read_text(encoding="utf-8"),
            K.render_component_map(ROOT),
        )

    def test_the_evidence_root_inputs_are_untouched(self) -> None:
        """U6 extends the generator; it must not move what the audit ran on."""
        unavailable = _evidence_root_unavailable()
        if unavailable:
            self.skipTest(unavailable)
        for path in (
            "config/scrna_observation_map.tsv",
            "docs/scrna/node_rna_interpretability.tsv",
        ):
            shown = _git("show", f"{EVIDENCE_ROOT}:{path}")
            self.assertIsNotNone(shown)
            self.assertEqual(
                shown.returncode, 0, f"{path} does not exist at {EVIDENCE_ROOT}"
            )
            self.assertEqual((ROOT / path).read_bytes(), shown.stdout, path)

    def test_the_committed_component_map_validates(self) -> None:
        rows = K.load_component_map(ROOT / K.COMPONENT_MAP)
        self.assertEqual(len(rows), 126)


class NodeSemantics(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        text = (ROOT / "docs/u6_semantics/node_semantics.tsv").read_text("utf-8")
        cls.rows = {r["model_node"]: r for r in _tsv(text)}

    def test_every_node_of_the_map_and_of_v051_has_one_row(self) -> None:
        from dt_adoc.scrna.node_support_contract import observation_rows

        self.assertEqual(len(self.rows), 59)
        self.assertEqual(set(self.rows), {r["model_node"] for r in observation_rows()})
        dictionary = (
            ROOT / "models/superset/adoc-literature-superset-v0.5.1/node_dictionary.tsv"
        )
        with dictionary.open(newline="", encoding="utf-8") as handle:
            nodes = {row["node_id"] for row in csv.DictReader(handle, delimiter="\t")}
        self.assertEqual(set(self.rows), nodes)

    def test_assessable_rows_agree_with_the_frozen_axes_table(self) -> None:
        frozen_text = (ROOT / "docs/scrna/node_rna_interpretability.tsv").read_text(
            encoding="utf-8"
        )
        frozen = {r["model_node"]: r for r in _tsv(frozen_text.replace("\r\n", "\n"))}
        self.assertEqual(len(frozen), 27)
        for node, want in frozen.items():
            got = self.rows[node]
            for field in (
                "compartment",
                "measurement_type",
                "presence_can_establish",
                "convincing_absence_can_establish",
                "not_blind",
            ):
                self.assertEqual(got[field], want[field], (node, field))

    def test_not_rna_assessable_is_its_own_state_for_the_other_32(self) -> None:
        unassessable = [
            r
            for r in self.rows.values()
            if r["measurement_type"] == "not_RNA_assessable"
        ]
        self.assertEqual(len(unassessable), 32)
        for row in unassessable:
            self.assertEqual(row["measurement_observability"], "not_observable")
            self.assertEqual(row["presence_can_establish"], "not_applicable")
            self.assertEqual(row["convincing_absence_can_establish"], "not_applicable")
            self.assertEqual(row["requirement_structure"], "not_applicable")

    def test_only_klf12_is_not_blind(self) -> None:
        """T-F: the tag reaches every consumer of the semantics view."""
        self.assertEqual(
            {n for n, r in self.rows.items() if r["not_blind"] == "true"},
            {"E_KLF12_HIGH"},
        )

    def test_no_requirement_structure_is_declared(self) -> None:
        """§6.2: no cited source states one, so none is invented."""
        self.assertEqual(K.DECLARED_REQUIREMENTS, {})
        structures = {
            n: r["requirement_structure"]
            for n, r in self.rows.items()
            if r["measurement_type"] != "not_RNA_assessable"
        }
        self.assertEqual(
            {n for n, s in structures.items() if s != "undeclared"}, {"E_CD98_CD9"}
        )
        self.assertEqual(structures["E_CD98_CD9"], "requires_definition")

    def test_the_view_carries_no_model_version_property(self) -> None:
        from dt_adoc.scrna.observability import SEMANTICS_FIELDS

        for field in ("v04_function_class", "phenotype_inert", "evidence_class"):
            self.assertNotIn(field, SEMANTICS_FIELDS)


class EvidenceEnum(unittest.TestCase):
    def test_the_frozen_labels_map_as_section_1_2_states(self) -> None:
        self.assertEqual(K.evidence_from_support("robustly_detected").state, S.PRESENT)
        self.assertEqual(
            K.evidence_from_support("sparse_or_low").state, S.INDETERMINATE
        )
        self.assertEqual(
            K.evidence_from_support("not_RNA_assessable").state, S.NOT_ASSESSABLE
        )
        absent = K.evidence_from_support(
            "not_detected_with_power", provisional=K.PROVISIONAL_FLAG
        )
        self.assertEqual((absent.state, absent.provisional), (S.ABSENT_POWERED, True))

    def test_failed_and_undefined_integrity_controls_stay_distinct(self) -> None:
        failed = K.evidence_from_support("uninformative", "uninformative_integrity")
        undefined = K.evidence_from_support(
            "uninformative", "uninformative_no_integrity_control"
        )
        self.assertEqual(failed.state, undefined.state)
        self.assertEqual(failed.state, S.INDETERMINATE)
        self.assertNotEqual(failed, undefined)
        self.assertEqual(failed.reason, "uninformative_integrity")
        self.assertEqual(undefined.reason, "uninformative_no_integrity_control")

    def test_the_vocabulary_matches_what_node_support_can_emit(self) -> None:
        source = (ROOT / "src/dt_adoc/scrna/node_support.py").read_text("utf-8")
        for reason in K.UNINFORMATIVE_REASONS:
            self.assertIn(f'"{reason}"', source)
        for label in ("robustly_detected", "sparse_or_low", "not_detected_with_power"):
            self.assertIn(f'"{label}"', source)

    def test_every_committed_support_call_maps(self) -> None:
        import json

        payload = json.loads(
            (ROOT / "docs/scrna/node_support_findings.json").read_text("utf-8")
        )
        for arms in payload["node_support"].values():
            for call in arms.values():
                K.evidence_from_support(
                    call["label"], call.get("reason", ""), call.get("provisional", "")
                )

    def test_the_mapping_is_closed(self) -> None:
        with self.assertRaises(ComponentMapError):
            K.evidence_from_support("detected")
        with self.assertRaises(ComponentMapError):
            K.evidence_from_support("uninformative", "uninformative_other")
        with self.assertRaises(ComponentMapError):
            K.evidence_from_support("robustly_detected", provisional=K.PROVISIONAL_FLAG)
        with self.assertRaises(ComponentMapError):
            Evidence(S.INDETERMINATE, "x", provisional=True)


def _spec(logic: str, parts: tuple[Evidence, ...]) -> tuple[S, bool]:
    """§6.3 restated independently of the implementation, rule by rule."""
    states = [p.state for p in parts]
    absent = [p for p in parts if p.state is S.ABSENT_POWERED]
    if logic == AND:
        if absent:
            return S.ABSENT_POWERED, all(p.provisional for p in absent)
        if S.NOT_ASSESSABLE in states:
            return S.NOT_ASSESSABLE, False
        if S.INDETERMINATE in states:
            return S.INDETERMINATE, False
        return S.PRESENT, False
    if S.PRESENT in states:
        return S.PRESENT, False
    if S.NOT_ASSESSABLE in states:
        return S.NOT_ASSESSABLE, False
    if S.INDETERMINATE in states:
        return S.INDETERMINATE, False
    return S.ABSENT_POWERED, any(p.provisional for p in absent)


ALPHABET: tuple[Evidence, ...] = (
    Evidence(S.PRESENT, "p"),
    Evidence(S.INDETERMINATE, "i"),
    Evidence(S.NOT_ASSESSABLE, "n"),
    Evidence(S.ABSENT_POWERED, "a"),
    Evidence(S.ABSENT_POWERED, "a*", provisional=True),
)


class Combinator(unittest.TestCase):
    def test_total_over_every_tuple_up_to_four_components(self) -> None:
        """T-D: 4^k states, and both provenance values on every absence."""
        for logic in (AND, OR):
            for k in range(1, 5):
                for parts in itertools.product(ALPHABET, repeat=k):
                    got = K.combine(logic, parts)
                    self.assertEqual((got.state, got.provisional), _spec(logic, parts))

    def test_commutative_associative_idempotent_under_nesting(self) -> None:
        """On the (state, provisional) projection only; `reason` is a trace."""
        key = K.evidence_key

        for logic in (AND, OR):
            for a, b, c in itertools.product(ALPHABET, repeat=3):
                self.assertEqual(
                    key(K.combine(logic, (a, b))), key(K.combine(logic, (b, a)))
                )
                self.assertEqual(key(K.combine(logic, (a, a))), key(a))
                left = K.combine(logic, (K.combine(logic, (a, b)), c))
                right = K.combine(logic, (a, K.combine(logic, (b, c))))
                self.assertEqual(key(left), key(right))

    def test_the_reason_is_an_order_preserving_trace_outside_the_algebra(self) -> None:
        """Equal evidence, different trace: the contract is `evidence_key`."""
        a, b = Evidence(S.PRESENT, "p"), Evidence(S.INDETERMINATE, "i")
        forward, backward = K.combine(AND, (a, b)), K.combine(AND, (b, a))
        self.assertEqual(K.evidence_key(forward), K.evidence_key(backward))
        self.assertEqual((forward.reason, backward.reason), ("AND[p,i]", "AND[i,p]"))

    def test_the_operators_are_not_de_morgan_duals(self) -> None:
        """§6.3(1): NOT_ASSESSABLE outranks INDETERMINATE in BOTH operators."""
        pair = (Evidence(S.NOT_ASSESSABLE, "n"), Evidence(S.INDETERMINATE, "i"))
        self.assertEqual(K.combine(AND, pair).state, S.NOT_ASSESSABLE)
        self.assertEqual(K.combine(OR, pair).state, S.NOT_ASSESSABLE)

    def test_empty_groups_raise(self) -> None:
        for logic in (AND, OR):
            with self.assertRaises(ComponentMapError):
                K.combine(logic, ())
        with self.assertRaises(ComponentMapError):
            K.combine("XOR", ALPHABET[:1])

    def test_no_arithmetic_or_ordering_on_evidence_states(self) -> None:
        """T-D: the combinator never treats the states as ordered numbers."""
        tree = ast.parse(inspect.getsource(K.combine))
        banned_calls = {"min", "max", "sum", "sorted", "int", "float"}
        for node in ast.walk(tree):
            self.assertNotIsInstance(node, ast.BinOp)
            if isinstance(node, ast.Compare):
                for op in node.ops:
                    self.assertNotIsInstance(op, (ast.Lt, ast.Gt, ast.LtE, ast.GtE))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, banned_calls)
        for state in S:
            self.assertIsInstance(state.value, str)

    def test_combined_reason_keeps_every_component_reason(self) -> None:
        got = K.combine(
            AND,
            (
                Evidence(S.INDETERMINATE, "uninformative_integrity"),
                Evidence(S.INDETERMINATE, "uninformative_no_integrity_control"),
            ),
        )
        self.assertIn("uninformative_integrity", got.reason)
        self.assertIn("uninformative_no_integrity_control", got.reason)


class ProvisionalAbsencesNeverClamp(unittest.TestCase):
    """T-E2, on synthetic fixtures: the committed audit has no absence at all."""

    confirmed = Evidence(S.ABSENT_POWERED, "a")
    provisional = Evidence(S.ABSENT_POWERED, "a*", provisional=True)

    def test_and_is_provisional_only_if_every_absence_is(self) -> None:
        both = K.combine(AND, (self.provisional, self.provisional))
        mixed = K.combine(AND, (self.provisional, self.confirmed))
        self.assertTrue(both.provisional)
        self.assertFalse(mixed.provisional)
        self.assertFalse(K.clamp_permitted_by_evidence(both))
        self.assertTrue(K.clamp_permitted_by_evidence(mixed))

    def test_or_is_provisional_if_any_absence_is(self) -> None:
        mixed = K.combine(OR, (self.provisional, self.confirmed))
        self.assertEqual(mixed.state, S.ABSENT_POWERED)
        self.assertTrue(mixed.provisional)
        self.assertFalse(K.clamp_permitted_by_evidence(mixed))

    def test_the_flag_survives_nesting(self) -> None:
        tree = Group(AND, ("A", Group(OR, ("B", "C"))))
        got = K.evaluate(
            tree,
            {
                "A": Evidence(S.PRESENT, "p"),
                "B": self.provisional,
                "C": self.confirmed,
            },
        )
        self.assertEqual((got.state, got.provisional), (S.ABSENT_POWERED, True))
        self.assertFalse(K.clamp_permitted_by_evidence(got))

    def test_nothing_but_a_confirmed_absence_permits_a_clamp(self) -> None:
        for evidence in ALPHABET:
            self.assertEqual(
                K.clamp_permitted_by_evidence(evidence), evidence is ALPHABET[3]
            )


class UndeclaredStructureIsInert(unittest.TestCase):
    def test_undeclared_and_requires_definition_evaluate_indeterminate(self) -> None:
        """T-J."""
        for structure in (K.UNDECLARED, K.REQUIRES_DEFINITION):
            got = K.evaluate(structure, {})
            self.assertEqual(got.state, S.INDETERMINATE)
            self.assertFalse(K.clamp_permitted_by_evidence(got))
        self.assertEqual(K.evaluate(K.NOT_APPLICABLE, {}).state, S.NOT_ASSESSABLE)
        with self.assertRaises(ComponentMapError):
            K.evaluate("declared", {})

    def test_a_component_without_evidence_raises(self) -> None:
        with self.assertRaises(ComponentMapError):
            K.evaluate(Group(AND, ("A",)), {})


def _row(**fields: str) -> dict[str, str]:
    row = {f: "" for f in K.COMPONENT_FIELDS}
    row.update(
        model_node="X_SYNTHETIC",
        requirement_set="node_level",
        requirement_structure="declared",
        role="availability_requirement",
        committed_symbol_status="present_in_audited_namespace",
        alias_resolution="not_applicable",
        current_symbol_presence="not_applicable",
        source="synthetic fixture",
    )
    row.update(fields)
    if not row["symbol_as_committed"]:
        for field in K._SYMBOL_PROVENANCE_FIELDS:
            row.setdefault(field, "")
            if field not in fields:
                row[field] = ""
    return row


def _integrin_shaped() -> list[dict[str, str]]:
    """A MIN(A, MAX(C, D)) shape. Synthetic: no committed node declares one."""
    return [
        _row(requirement_group="g1", logic=AND),
        _row(requirement_group="g2", parent_group="g1", logic=OR),
        _row(requirement_group="g1", symbol_as_committed="A"),
        _row(requirement_group="g2", symbol_as_committed="C"),
        _row(requirement_group="g2", symbol_as_committed="D"),
    ]


class ComponentMapSchema(unittest.TestCase):
    def test_a_declared_nested_structure_assembles_and_evaluates(self) -> None:
        rows = _integrin_shaped()
        K.validate_component_rows(rows)
        tree = K.group_tree(("X_SYNTHETIC", ""), rows)
        self.assertEqual(tree, Group(AND, ("A", Group(OR, ("C", "D")))))
        evidence = {
            "A": Evidence(S.PRESENT, "p"),
            "C": Evidence(S.ABSENT_POWERED, "a"),
            "D": Evidence(S.PRESENT, "p"),
        }
        self.assertEqual(K.evaluate(tree, evidence).state, S.PRESENT)
        evidence["A"] = Evidence(S.ABSENT_POWERED, "a")
        self.assertEqual(K.evaluate(tree, evidence).state, S.ABSENT_POWERED)

    def test_an_empty_group_raises_at_load(self) -> None:
        rows = _integrin_shaped()[:2] + [
            _row(requirement_group="g1", symbol_as_committed="A")
        ]
        with self.assertRaises(ComponentMapError):
            K.validate_component_rows(rows)

    def test_malformed_trees_raise(self) -> None:
        cases = {
            "two roots": _integrin_shaped()
            + [
                _row(requirement_group="g3", logic=OR),
                _row(requirement_group="g3", symbol_as_committed="E"),
            ],
            "unknown group": _integrin_shaped()
            + [_row(requirement_group="g9", symbol_as_committed="E")],
            "unreachable cycle": _integrin_shaped()
            + [
                _row(requirement_group="g5", parent_group="g6", logic=OR),
                _row(requirement_group="g6", parent_group="g5", logic=OR),
                _row(requirement_group="g5", symbol_as_committed="E"),
                _row(requirement_group="g6", symbol_as_committed="F"),
            ],
            "declared twice": _integrin_shaped()
            + [_row(requirement_group="g2", logic=AND)],
            "no group at all": [_row(requirement_group="", symbol_as_committed="A")],
        }
        for name, rows in cases.items():
            with self.subTest(name), self.assertRaises(ComponentMapError):
                K.validate_component_rows(rows)

    def test_malformed_provenance_and_hierarchy_raise(self) -> None:
        """Each probe the independent review reproduced as accepted."""
        blank_source = _integrin_shaped()
        blank_source[0]["source"] = ""
        component_with_parent = _integrin_shaped()
        component_with_parent[2]["parent_group"] = "g2"
        component_with_logic = _integrin_shaped()
        component_with_logic[3]["logic"] = AND
        id_without_symbol = [
            _row(
                requirement_structure="undeclared",
                role="support_feature",
                symbol_as_committed="A",
                hgnc_id="HGNC:1",
            )
        ]
        symbol_without_id = [
            _row(
                requirement_structure="undeclared",
                role="support_feature",
                symbol_as_committed="A",
                current_hgnc_symbol="B",
            )
        ]
        grouped_support = [
            _row(
                requirement_structure="undeclared",
                role="support_feature",
                symbol_as_committed="A",
                requirement_group="g1",
            )
        ]
        group_with_status = _integrin_shaped()
        group_with_status[0]["hgnc_id"] = "HGNC:1"
        cases = {
            "blank source": blank_source,
            "parent_group on a component": component_with_parent,
            "logic on a component": component_with_logic,
            "hgnc_id without a symbol": id_without_symbol,
            "current symbol without an id": symbol_without_id,
            "support feature in a group": grouped_support,
            "symbol status on a group row": group_with_status,
        }
        for name, rows in cases.items():
            with self.subTest(name), self.assertRaises(ComponentMapError):
                K.validate_component_rows(rows)

    def test_availability_rows_cannot_sit_on_an_undeclared_structure(self) -> None:
        rows = [
            _row(
                requirement_structure="undeclared",
                requirement_group="g1",
                symbol_as_committed="A",
            )
        ]
        with self.assertRaises(ComponentMapError):
            K.validate_component_rows(rows)

    def test_a_variant_set_names_its_variant(self) -> None:
        with self.assertRaises(ComponentMapError):
            K.validate_component_rows(
                [
                    _row(
                        requirement_set="variant",
                        requirement_structure="undeclared",
                        role="support_feature",
                        symbol_as_committed="A",
                    )
                ]
            )
        with self.assertRaises(ComponentMapError):
            K.validate_component_rows(
                [
                    _row(
                        variant_id="GP130-b",
                        requirement_structure="undeclared",
                        role="support_feature",
                        symbol_as_committed="A",
                    )
                ]
            )

    def test_a_variant_set_must_name_a_variant_the_governing_model_declares(
        self,
    ) -> None:
        def variant_row(node: str, variant: str) -> dict[str, str]:
            return _row(
                model_node=node,
                requirement_set="variant",
                variant_id=variant,
                requirement_structure="undeclared",
                role="support_feature",
                symbol_as_committed="A",
            )

        self.assertIn(
            ("hand2_required_decidual_variant", "S_DECIDUALIZED"),
            K.declared_variants(ROOT),
        )
        K.validate_component_rows(
            [variant_row("S_DECIDUALIZED", "hand2_required_decidual_variant")]
        )
        for name, row in {
            "unknown id": variant_row("E_GP130_STAT3", "DOES_NOT_EXIST"),
            "declared for another node": variant_row(
                "E_GP130_STAT3", "hand2_required_decidual_variant"
            ),
        }.items():
            with self.subTest(name), self.assertRaises(ComponentMapError):
                K.validate_component_rows([row])

    def test_availability_and_direction_roles_stay_apart_for_gp130(self) -> None:
        """§6.1: STAT3 is measured but, by R2, never votes on direction."""
        rows = K.load_component_map(ROOT / K.COMPONENT_MAP)
        support = K.usable_feature_symbols(rows, "E_GP130_STAT3", "support_feature")
        direction = K.usable_feature_symbols(rows, "E_GP130_STAT3", "direction_readout")
        self.assertEqual(support, ("SOCS3", "BCL3", "STAT3"))
        self.assertEqual(direction, ("SOCS3", "BCL3"))


class HgncOwnerDecision(unittest.TestCase):
    """T-E and the U6 owner decision of 2026-09-23 on CTGF/CYR61."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = K.load_component_map(ROOT / K.COMPONENT_MAP)

    def test_the_frozen_audit_still_records_both_symbols_absent(self) -> None:
        self.assertEqual(K.absent_features(ROOT), {"CTGF", "CYR61"})

    def test_the_resolution_table_is_exactly_the_two_decided_renames(self) -> None:
        self.assertEqual(
            K.HGNC_PREVIOUS_SYMBOL_RESOLUTIONS,
            {"CTGF": ("CCN2", "HGNC:2500"), "CYR61": ("CCN1", "HGNC:2654")},
        )
        self.assertLessEqual(
            set(K.HGNC_PREVIOUS_SYMBOL_RESOLUTIONS), set(K.absent_features(ROOT))
        )

    def test_absent_symbols_are_recorded_with_every_field_kept_separate(self) -> None:
        resolved = [r for r in self.rows if r["alias_resolution"] == "verified_rename"]
        self.assertEqual(len(resolved), 4)  # two symbols x two roles
        for row in resolved:
            self.assertEqual(row["model_node"], "S_TAZ_ECM")
            self.assertEqual(row["committed_symbol_status"], "feature_absent")
            self.assertEqual(row["current_symbol_presence"], "unverified")
            current, hgnc_id = K.HGNC_PREVIOUS_SYMBOL_RESOLUTIONS[
                row["symbol_as_committed"]
            ]
            self.assertEqual(
                (row["current_hgnc_symbol"], row["hgnc_id"]), (current, hgnc_id)
            )
        present = [
            r
            for r in self.rows
            if r["committed_symbol_status"] == "present_in_audited_namespace"
        ]
        for row in present:
            self.assertEqual(row["alias_resolution"], "not_applicable")
            self.assertEqual(row["current_hgnc_symbol"], "")

    def test_no_alias_resolved_feature_is_usable_yet(self) -> None:
        self.assertEqual(
            K.usable_feature_symbols(self.rows, "S_TAZ_ECM"), ("WWTR1", "FN1", "COL4A1")
        )
        self.assertNotIn("verified", K.CURRENT_SYMBOL_PRESENCE)
        for row in self.rows:
            if row["committed_symbol_status"] == "feature_absent":
                self.assertNotIn(
                    row["symbol_as_committed"],
                    K.usable_feature_symbols(self.rows, row["model_node"], row["role"]),
                )

    def test_a_resolution_for_a_present_symbol_is_refused(self) -> None:
        rows = [
            _row(
                requirement_structure="undeclared",
                role="support_feature",
                symbol_as_committed="WWTR1",
                current_hgnc_symbol="WWTR1",
                hgnc_id="HGNC:24042",
                alias_resolution="verified_rename",
                current_symbol_presence="unverified",
            )
        ]
        with self.assertRaises(ComponentMapError):
            K.validate_component_rows(rows)


class GeneratorCommandLine(unittest.TestCase):
    """Which generator runs is decided by the arguments, and only exactly."""

    def _run(self, argv: list[str]) -> tuple[int | None, list[str]]:
        import contextlib
        from unittest import mock

        from dt_adoc.scrna import observability as O

        calls: list[str] = []
        with (
            mock.patch.object(O, "write_map", lambda: calls.append("map") or Path("m")),
            mock.patch.object(O, "load_scrna_observation_map", list),
            mock.patch.object(
                O,
                "write_semantics",
                lambda: calls.append("u6") or (Path("s"), Path("c")),
            ),
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            try:
                code = O.main(argv)
            except SystemExit as stop:
                code = stop.code
        return code, calls

    def test_no_arguments_keeps_the_historical_map_generator(self) -> None:
        self.assertEqual(self._run([]), (0, ["map"]))

    def test_the_exact_flag_runs_only_the_u6_generator(self) -> None:
        self.assertEqual(self._run(["--u6-semantics"]), (0, ["u6"]))

    def test_anything_else_fails_without_running_either_generator(self) -> None:
        for argv in (
            ["--u6-semantic"],  # a prefix, which argparse would accept by default
            ["--u6-semantics-x"],
            ["u6-semantics"],
            ["--u6-semantics", "extra"],
        ):
            with self.subTest(argv=argv):
                code, calls = self._run(argv)
                self.assertNotEqual(code, 0)
                self.assertEqual(calls, [])


class ImportBoundary(unittest.TestCase):
    def test_components_import_no_simulation_or_scoring_module(self) -> None:
        """T-C, applied to the combinator this unit adds."""
        tree = ast.parse((ROOT / "src/dt_adoc/scrna/components.py").read_text("utf-8"))
        banned = (
            "simulation",
            "concordance",
            "calibration",
            "scoring",
            "perturbations",
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                self.assertFalse(
                    any(f"dt_adoc.{b}" in node.module for b in banned), node.module
                )


if __name__ == "__main__":
    unittest.main()
