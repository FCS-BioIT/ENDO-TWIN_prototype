"""G12: effect-level scientific licensing of direct rows (O8b) and the O8c policy.

``docs/o8b_direct_effect_governance.md`` pre-registers what is tested here. A
``direct_supported_effect`` row runs only with exactly one approved ledger row
under its own ``(intervention_id, model_version, target_node, mode)``, citing
the same evidence and bound to the row's digest, on a target the O8c policy
admits. Every approval here is synthetic and lives in a sandbox copy of the
ledger; the committed ledger holds none.

Since Stage 4b the synthetic compounds are v0.6.0 rows, each with a synthetic
target declaration, because a direct row on a version with no entity map or
expressivity artefact is refused (``docs/stage4b_direct_admission.md`` §6.1,
§6.6). The O8b checks run before the Stage 4b ones, so every refusal here still
fails for its own rule; the Stage 4b rules themselves are gate G13
(``tests/unit/test_stage4b_admission.py``).

The runtime half (provenance and the N+1 contract) is
``tests/integration/test_markerless_intervention_runtime.py``.
"""

from __future__ import annotations

import csv
import dataclasses
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.perturbations import adjudication, engine
from dt_adoc.perturbations.adjudication import (
    ADJUDICATION_COLUMNS,
    ADJUDICATIONS_PATH,
    AUDIT_PATH,
    DECLARATION_COLUMNS,
    TARGET_POLICY_PATH,
    _sha256,
    library_row_digest,
    library_rows_digest,
    render_audit,
    target_audit,
)
from dt_adoc.perturbations.engine import (
    DIRECT_BASIS,
    LIBRARY_COLUMNS,
    InterventionEffect,
    InterventionError,
    load_intervention_library,
    named_effect_records,
)

_spec = importlib.util.spec_from_file_location(
    "o8_sandbox", ROOT / "tests/fixtures/o8_markerless/sandbox.py"
)
sandbox = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sandbox)

FIXTURE = ROOT / "tests/fixtures/o8_markerless"
V052 = "adoc-literature-superset-v0.5.2"
V060 = "adoc-literature-superset-v0.6.0"


def _line(name: str) -> str:
    return (FIXTURE / name).read_text(encoding="utf-8").splitlines()[0]


X_ROW = _line("synthetic_compound_x.library.tsv")
X_APPROVAL = _line("synthetic_compound_x.adjudication.tsv")
X_DECLARATION = _line("synthetic_compound_x.declaration.tsv")


def _replace(row: str, columns: tuple[str, ...], **fields: str) -> str:
    values = row.split("\t")
    for name, value in fields.items():
        values[columns.index(name)] = value
    return "\t".join(values)


def _effect(row: str) -> InterventionEffect:
    values = dict(zip(LIBRARY_COLUMNS, row.split("\t")))
    for column in ("legacy_perturbation_ids", "abstraction_sources", "evidence_ids"):
        values[column] = tuple(
            p.strip() for p in values[column].split(";") if p.strip()
        )
    return InterventionEffect(**values)


class _Sandbox(unittest.TestCase):
    """One sandbox root per test, so an edit never leaks into the next."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = sandbox.build_sandbox(Path(self._tmp.name))
        self.addCleanup(self._tmp.cleanup)

    def append(self, path: Path, row: str) -> None:
        with (self.root / path).open("a", encoding="utf-8") as handle:
            handle.write(row + "\n")

    def row(self, **fields: str) -> str:
        """X's library row with some columns replaced."""
        return _replace(X_ROW, LIBRARY_COLUMNS, **fields)

    def declaration(self, library_row: str | None = None, **fields: str) -> str:
        """X's declaration, re-bound to ``library_row`` when given, so that a
        changed row is refused by the rule under test and not by C2."""
        if library_row is not None:
            effect = _effect(library_row)
            fields = {
                "intervention_id": effect.intervention_id,
                "model_version": effect.model_version,
                "declared_targets": effect.target_node,
                "library_rows_sha256": library_rows_digest([effect]),
                **fields,
            }
        return _replace(X_DECLARATION, DECLARATION_COLUMNS, **fields)

    def approval(self, library_row: str | None = None, **fields: str) -> str:
        """X's approval, re-bound to ``library_row`` and to its re-bound
        declaration when given, so C8 does not fire instead."""
        if library_row is not None:
            effect = _effect(library_row)
            fields = {
                "intervention_id": effect.intervention_id,
                "model_version": effect.model_version,
                "target_node": effect.target_node,
                "mode": effect.mode,
                "evidence_ids": ";".join(effect.evidence_ids),
                "library_row_sha256": library_row_digest(effect),
                "target_declaration_sha256": _sha256(self.declaration(library_row)),
                **fields,
            }
        return _replace(X_APPROVAL, ADJUDICATION_COLUMNS, **fields)

    def add_x(
        self,
        *,
        approval: str | None = None,
        row: str | None = None,
        declaration: str | None = None,
        current: bool = False,
    ) -> None:
        """X's evidence, then a declaration, an approval and a library row.

        The declaration defaults to X's, re-bound to ``row`` when one is given.
        ``current`` regenerates the expressivity artefact after the row, as an
        admission must; a test of an O8b refusal leaves it alone, since those
        rules are checked first and a malformed row need not be one the
        generator can read.
        """
        sandbox.add_compound(self.root, "synthetic_compound_x", ("evidence",))
        self.append(
            sandbox.DECLARATIONS,
            declaration if declaration is not None else self.declaration(row),
        )
        if approval is not None:
            self.append(ADJUDICATIONS_PATH, approval)
        if row is not None:
            self.append(sandbox.LIBRARY, row)
            if current:
                sandbox.regenerate_expressivity(self.root)

    def load(self):
        return load_intervention_library(self.root)

    def refused(self, pattern: str) -> None:
        with self.assertRaisesRegex(InterventionError, pattern):
            self.load()


class ApprovalTest(_Sandbox):
    """What licenses a direct row, and what does not."""

    def test_an_approved_row_loads_and_carries_its_approval(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_x")
        (effect,) = self.load()["synthetic_compound_x"]
        self.assertEqual(effect.adjudication_id, "SYN-X-1")
        ledger = adjudication.load_adjudications(self.root)
        (entry,) = ledger.values()
        self.assertEqual(effect.adjudication_sha256, entry.row_sha256)
        self.assertEqual(entry.library_row_sha256, library_row_digest(effect))

    def test_a_multi_target_compound_with_every_effect_approved_runs(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_y")
        effects = self.load()["synthetic_compound_y"]
        self.assertEqual(
            {(e.target_node, e.adjudication_id) for e in effects},
            {("E_HBEGF", "SYN-Y-1"), ("S_TAZ_ECM", "SYN-Y-2")},
        )
        self.assertEqual(len({e.adjudication_sha256 for e in effects}), 2)

    def test_no_adjudication_is_refused(self) -> None:
        self.add_x(row=X_ROW)
        self.refused("no adjudication in config/direct_effect_adjudications.tsv")

    def test_verified_evidence_without_an_approval_is_refused(self) -> None:
        """Register status is not a licence, whatever it says."""
        self.add_x(row=self.row(evidence_ids="SOFIA-HT-002"))
        self.refused("no adjudication")

    def test_a_candidate_or_rejected_adjudication_is_refused(self) -> None:
        for decision in ("candidate", "rejected"):
            with self.subTest(decision=decision):
                self.setUp()
                self.add_x(approval=self.approval(decision=decision), row=X_ROW)
                self.refused(f"SYN-X-1 is {decision}, not approved_for_model_execution")

    def test_a_wrong_target_is_refused(self) -> None:
        """Approved for target A; the row is changed to target B."""
        self.add_x(approval=X_APPROVAL, row=self.row(target_node="E_HBEGF"))
        self.refused(
            r"no adjudication .* adjudicated for \['E_GP130_STAT3/activity_veto'\]"
        )

    def test_a_wrong_mode_is_refused(self) -> None:
        """A second direct mode, patched in: the approval names activity_veto."""
        with (
            mock.patch.object(engine, "MODES", (*engine.MODES, "activity_boost")),
            mock.patch.object(
                engine, "DIRECT_MODES", ("activity_veto", "activity_boost")
            ),
        ):
            self.add_x(approval=X_APPROVAL, row=self.row(mode="activity_boost"))
            self.refused("no adjudication .* for mode activity_boost")

    def test_an_approval_under_a_non_direct_mode_is_refused(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_x")
        self.append(
            ADJUDICATIONS_PATH,
            self.approval(adjudication_id="SYN-X-2", mode="no_executable_effect"),
        )
        self.refused("is not a direct mode")

    def test_a_wrong_model_version_is_refused(self) -> None:
        """Approved for v0.5.2; the row executes on v0.6.0."""
        self.add_x(approval=self.approval(model_version=V052), row=X_ROW)
        self.refused("no adjudication")

    def test_an_approval_for_v060_does_not_license_v052(self) -> None:
        row = self.row(model_version=V052)
        self.add_x(approval=X_APPROVAL, row=row)
        self.refused(
            r"synthetic_compound_x -> E_GP130_STAT3 \(adoc-literature-superset-v0.5.2\): no adjudication"
        )

    def test_a_fully_approved_row_on_a_version_without_an_entity_map_is_refused(
        self,
    ) -> None:
        """Why the fixtures moved to v0.6.0: every O8b condition holds on v0.5.2,
        and Stage 4b still refuses, because v0.5.2 has no entity map rows and no
        expressivity artefact."""
        row = self.row(model_version=V052)
        self.add_x(approval=self.approval(row), row=row)
        self.refused(f"has no {V052} rows")

    def test_mismatching_evidence_ids_are_refused(self) -> None:
        # The row cites a second id; the approval covers only the first.
        sandbox.add_compound(self.root, "synthetic_compound_y", ("evidence",))
        self.add_x(
            approval=X_APPROVAL,
            row=self.row(evidence_ids="SYNTHETIC-O8-X;SYNTHETIC-O8-Y"),
        )
        self.refused(r"cites evidence .* but SYN-X-1 approved \['SYNTHETIC-O8-X'\]")

    def test_an_approval_citing_other_evidence_is_refused(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_y", ("evidence",))
        self.add_x(approval=self.approval(evidence_ids="SYNTHETIC-O8-Y"), row=X_ROW)
        self.refused("cites evidence")

    def test_a_changed_row_invalidates_its_approval(self) -> None:
        """Abstraction, claim boundary, label, class and sources are bound by the
        digest, which the approval was written against."""
        changes = {
            "model_abstraction": "Synthetic: something else",
            "claim_boundary": "A different boundary",
            "intervention_label": "Synthetic compound X, renamed",
            "abstraction_sources": "tests/fixtures/o8_markerless/README.md#other",
        }
        for column, value in changes.items():
            with self.subTest(column=column):
                self.setUp()
                self.add_x(approval=X_APPROVAL, row=self.row(**{column: value}))
                self.refused("the library row changed since SYN-X-1 approved it")

    def test_unresolved_evidence_is_refused_even_with_an_approval(self) -> None:
        self.append(ADJUDICATIONS_PATH, X_APPROVAL)
        self.append(sandbox.LIBRARY, X_ROW)
        self.refused("not in context/evidence")

    def test_a_missing_source_is_refused_even_with_an_approval(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_x")
        (self.root / sandbox.FIXTURE_RELATIVE / "README.md").unlink()
        self.refused("does not exist")

    def test_a_mechanically_illegal_target_is_refused_even_with_an_approval(
        self,
    ) -> None:
        row = self.row(target_node="IN_E2")
        self.add_x(approval=self.approval(row), row=row)
        self.refused("is an input node")

    def test_a_policy_refused_role_is_refused_even_with_an_approval(self) -> None:
        for target, role in (
            ("E_PAEP", "readout"),
            ("E_SECRETORY_STATE", "state"),
            ("E_RECEPTIVE_SURFACE", "latent_state"),
            ("X_ADHESION_ROUTE_SPP1", "interface_route"),
            ("S_BMP2", "regulator_or_readout"),
            ("OUT_STABLE_ADHESION", "phenotype"),
        ):
            with self.subTest(target=target):
                self.setUp()
                row = self.row(target_node=target)
                self.add_x(approval=self.approval(row), row=row)
                self.refused(f"may not target a {role} node")

    def test_a_node_policy_refusal_is_refused_even_with_an_approval(self) -> None:
        for target in (
            "E_DAG1_CLEAVED",
            "E_DAG1_FULL",
            "E_MUC1_SLEX",
            "E_MUC1_BARRIER",
        ):
            with self.subTest(target=target):
                self.setUp()
                row = self.row(target_node=target)
                self.add_x(approval=self.approval(row), row=row)
                self.refused(f"{target} is refused by node policy")

    def test_an_unlisted_role_is_refused(self) -> None:
        dictionary = self.root / "models/superset" / V060 / "node_dictionary.tsv"
        text = dictionary.read_text(encoding="utf-8")
        old = "\tpathway_gate\t"
        self.assertEqual(text.count(old), 1)
        dictionary.write_text(text.replace(old, "\tnew_role\t"), encoding="utf-8")
        sandbox.add_compound(self.root, "synthetic_compound_x")
        self.refused("role 'new_role' is not in config/direct_effect_target_policy.tsv")

    def test_a_partially_approved_multi_target_compound_is_refused(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_y", ("evidence", "library"))
        first = (
            (FIXTURE / "synthetic_compound_y.adjudication.tsv")
            .read_text(encoding="utf-8")
            .splitlines()[0]
        )
        self.append(ADJUDICATIONS_PATH, first)
        self.refused(r"synthetic_compound_y -> S_TAZ_ECM .*: no adjudication")

    def test_an_approval_without_a_matching_row_licenses_nothing(self) -> None:
        self.add_x(approval=X_APPROVAL)
        library = self.load()
        self.assertNotIn("synthetic_compound_x", library)
        self.assertEqual(library, load_intervention_library(ROOT))


class LedgerTest(_Sandbox):
    """The ledger is validated as a whole, direct rows or not."""

    def test_a_duplicated_or_conflicting_key_is_refused(self) -> None:
        for decision in ("approved_for_model_execution", "rejected"):
            with self.subTest(decision=decision):
                self.setUp()
                sandbox.add_compound(self.root, "synthetic_compound_x")
                self.append(
                    ADJUDICATIONS_PATH,
                    self.approval(adjudication_id="SYN-X-2", decision=decision),
                )
                self.refused("SYN-X-1 already adjudicates")

    def test_a_repeated_adjudication_id_is_refused(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_x")
        self.append(ADJUDICATIONS_PATH, self.approval(target_node="E_HBEGF"))
        self.refused("a missing or repeated adjudication_id")

    def test_an_approval_attempting_target_inference_is_refused(self) -> None:
        for target in ("E_HBEGF;E_ITGAVB3_5", "E_*", "E_HBEGF or S_SPP1", ""):
            with self.subTest(target=target):
                self.setUp()
                self.add_x(approval=self.approval(target_node=target))
                self.refused("is not one node id")
        self.setUp()
        self.add_x(approval=self.approval(target_node="E_SOME_PROTEIN"))
        self.refused("E_SOME_PROTEIN is not a node of")

    def test_an_approval_naming_several_interventions_is_refused(self) -> None:
        self.add_x(approval=self.approval(intervention_id="x;y"))
        self.refused("must each name one item")

    def test_an_approval_for_a_legacy_or_migrated_intervention_is_refused(self) -> None:
        for intervention, version, target in (
            ("mifepristone", V052, "E_PGR"),
            ("anti_spp1", V060, "X_SPP1_LUMEN_FREE"),
        ):
            with self.subTest(intervention=intervention):
                self.setUp()
                self.add_x(
                    approval=self.approval(
                        intervention_id=intervention,
                        model_version=version,
                        target_node=target,
                    )
                )
                self.refused("only direct_supported_effect rows are adjudicated here")

    def test_an_approval_with_non_approvable_vocabulary_is_refused(self) -> None:
        for fields in (
            {
                "effect_evidence": "target_abundance_reduced",
                "system_match": "matches_model_compartment",
            },
            # A partial or graded reduction does not license a full veto: the
            # only executable mode abolishes the target and O4 is open.
            {
                "effect_evidence": "target_activity_partially_reduced",
                "system_match": "matches_model_compartment",
            },
            {
                "effect_evidence": "target_necessity_only",
                "system_match": "matches_model_compartment",
            },
            {"effect_evidence": "target_activity_reduced", "system_match": "non_human"},
            {
                "effect_evidence": "target_activity_reduced",
                "system_match": "synthetic_fixture",
            },
        ):
            with self.subTest(**fields):
                self.setUp()
                self.add_x(approval=self.approval(**fields))
                self.refused("an approval needs effect_evidence")

    def test_a_candidate_may_record_any_vocabulary(self) -> None:
        self.add_x(
            approval=self.approval(
                decision="candidate",
                effect_evidence="target_necessity_only",
                system_match="non_human",
            )
        )
        self.load()

    def test_unknown_vocabulary_is_refused(self) -> None:
        for column, pattern in (
            ("decision", "unknown decision"),
            ("effect_evidence", "unknown effect_evidence"),
            ("system_match", "unknown system_match"),
            ("system_grade", "unknown system_grade"),
        ):
            with self.subTest(column=column):
                self.setUp()
                self.add_x(approval=self.approval(**{column: "made_up"}))
                self.refused(pattern)

    def test_malformed_fields_are_refused(self) -> None:
        for fields, pattern in (
            ({"library_row_sha256": "abc"}, "not a sha256"),
            ({"dated": "3 Oct 2026"}, "not an ISO date"),
            ({"evidence_ids": ""}, "no evidence ids"),
            ({"rationale": ""}, "are required"),
            ({"target_declaration_sha256": "abc"}, "is not a sha256"),
            ({"target_declaration_sha256": ""}, "needs target_declaration_sha256"),
        ):
            with self.subTest(fields=fields):
                self.setUp()
                self.add_x(approval=self.approval(**fields))
                self.refused(pattern)

    def test_a_missing_basis_record_is_refused(self) -> None:
        self.add_x(approval=self.approval(basis_record="context/no_such_review.tsv#A"))
        self.refused("basis context/no_such_review.tsv#A does not exist")

    def test_a_synthetic_approval_of_real_evidence_is_refused(self) -> None:
        row = self.row(evidence_ids="SOFIA-HT-002")
        self.add_x(approval=self.approval(row), row=row)
        self.refused("a synthetic_fixture approval citing real evidence")

    def test_a_real_approval_of_synthetic_evidence_is_refused(self) -> None:
        # An approvable grade too, so the ledger's own §6.3 split does not
        # refuse it first.
        self.add_x(
            approval=self.approval(
                effect_evidence="target_activity_reduced",
                system_match="matches_model_compartment",
                system_grade="primary_human_endometrial",
            ),
            row=X_ROW,
        )
        self.refused("approves on synthetic evidence")

    def test_a_missing_ledger_refuses_a_direct_row(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_x")
        (self.root / ADJUDICATIONS_PATH).unlink()
        self.refused("need the adjudication ledger")

    def test_a_missing_ledger_does_not_touch_legacy_rows(self) -> None:
        (self.root / ADJUDICATIONS_PATH).unlink()
        self.assertEqual(self.load(), load_intervention_library(ROOT))

    def test_wrong_ledger_columns_are_refused(self) -> None:
        path = self.root / ADJUDICATIONS_PATH
        path.write_text("adjudication_id\tdecision\n", encoding="utf-8")
        self.refused("columns are")


class TargetPolicyTest(_Sandbox):
    def edit_policy(self, row: str) -> None:
        # The compound first: adding it regenerates the expressivity artefact,
        # which reads the policy, and the edit under test must reach the loader.
        sandbox.add_compound(self.root, "synthetic_compound_x")
        self.append(TARGET_POLICY_PATH, row)

    def test_a_missing_policy_refuses_a_direct_row(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_x")
        (self.root / TARGET_POLICY_PATH).unlink()
        self.refused("need the target policy")

    def test_a_node_row_may_only_refuse(self) -> None:
        self.edit_policy("node\tE_PAEP\teligible\tdocs/x.md\tadmit a readout")
        self.refused("a node row may only refuse")

    def test_unknown_policy_or_scope_is_refused(self) -> None:
        for row, pattern in (
            ("role\tnew_role\tmaybe\tdocs/x.md\tr", "unknown policy"),
            ("module\tMOD-01\trefused\tdocs/x.md\tr", "unknown scope"),
            ("role\tnew_role\trefused\t\tr", "basis and rationale are required"),
            ("role\treadout\teligible\tdocs/x.md\tr", "listed twice"),
        ):
            with self.subTest(row=row):
                self.setUp()
                self.edit_policy(row)
                self.refused(pattern)

    def test_a_node_refusal_narrows_but_a_role_row_decides_its_role(self) -> None:
        policy = adjudication.load_target_policy(ROOT)
        self.assertEqual(
            adjudication.policy_decision(policy, "E_DAG1_CLEAVED", "adhesion_support")[
                :2
            ],
            ("refused", "node"),
        )
        self.assertEqual(
            adjudication.policy_decision(policy, "E_HBEGF", "adhesion_support")[:2],
            ("eligible", "role"),
        )
        # A node refusal never changes a refused role's answer or scope.
        self.assertEqual(
            adjudication.policy_decision(policy, "E_DAG1_CLEAVED", "readout")[:2],
            ("refused", "role"),
        )


class DigestTest(unittest.TestCase):
    def test_every_library_column_is_bound(self) -> None:
        base = _effect(X_ROW)
        digest = library_row_digest(base)
        for column in LIBRARY_COLUMNS:
            value = getattr(base, column)
            changed = (*value, "extra") if isinstance(value, tuple) else value + "_"
            with self.subTest(column=column):
                self.assertNotEqual(
                    library_row_digest(dataclasses.replace(base, **{column: changed})),
                    digest,
                )

    def test_licensing_fields_are_not_part_of_the_row(self) -> None:
        base = _effect(X_ROW)
        self.assertEqual(
            library_row_digest(
                dataclasses.replace(
                    base,
                    adjudication_id="A",
                    adjudication_sha256="B",
                    parent_model_version="C",
                )
            ),
            library_row_digest(base),
        )

    def test_the_fixture_approvals_are_bound_to_the_fixture_rows(self) -> None:
        for compound in ("synthetic_compound_x", "synthetic_compound_y"):
            rows = (FIXTURE / f"{compound}.library.tsv").read_text().splitlines()
            approvals = (
                (FIXTURE / f"{compound}.adjudication.tsv").read_text().splitlines()
            )
            (declaration,) = (
                (FIXTURE / f"{compound}.declaration.tsv").read_text().splitlines()
            )
            digests = {library_row_digest(_effect(r)) for r in rows}
            approved = [
                dict(zip(ADJUDICATION_COLUMNS, a.split("\t"))) for a in approvals
            ]
            bound = {a["library_row_sha256"] for a in approved}
            self.assertEqual(bound, digests, compound)
            # Stage 4b: each approval names the declaration, and the declaration
            # names the rows.
            self.assertEqual(
                {a["target_declaration_sha256"] for a in approved},
                {_sha256(declaration)},
                compound,
            )
            self.assertEqual(
                dict(zip(DECLARATION_COLUMNS, declaration.split("\t")))[
                    "library_rows_sha256"
                ],
                library_rows_digest([_effect(r) for r in rows]),
                compound,
            )


class ProvenanceTest(_Sandbox):
    def test_different_approvals_give_different_records(self) -> None:
        """Same row, same network, two approvals that differ only in rationale."""
        records = []
        for rationale in ("first reading", "second reading"):
            self.setUp()
            self.add_x(
                approval=self.approval(rationale=rationale), row=X_ROW, current=True
            )
            records.append(
                named_effect_records(
                    ["synthetic_compound_x"], self.load(), model_version=V060
                )
            )
        (first,), (second,) = records
        self.assertEqual(first["adjudication_id"], second["adjudication_id"])
        self.assertNotEqual(first["adjudication_sha256"], second["adjudication_sha256"])
        self.assertEqual(first["target_node"], second["target_node"])

    def test_a_direct_record_names_its_approval(self) -> None:
        sandbox.add_compound(self.root, "synthetic_compound_x")
        (record,) = named_effect_records(
            ["synthetic_compound_x"], self.load(), model_version=V060
        )
        self.assertEqual(record["mapping_basis"], DIRECT_BASIS)
        self.assertEqual(record["model_version"], V060)
        self.assertEqual(record["adjudication_id"], "SYN-X-1")
        self.assertEqual(
            record["library_row_sha256"],
            dict(zip(ADJUDICATION_COLUMNS, X_APPROVAL.split("\t")))[
                "library_row_sha256"
            ],
        )

    def test_legacy_and_migrated_records_keep_their_shape(self) -> None:
        library = load_intervention_library(ROOT)
        legacy = named_effect_records(["anti_spp1"], library, model_version=V052)
        migrated = named_effect_records(["anti_spp1"], library, model_version=V060)
        base = {
            "intervention_id",
            "mapping_basis",
            "legacy_input_node",
            "target_node",
            "mode",
            "evidence_ids",
            "abstraction_sources",
            "claim_boundary",
        }
        self.assertEqual(set(legacy[0]), base)
        self.assertEqual(
            set(migrated[0]), base | {"model_version", "parent_model_version"}
        )
        for effects in library.values():
            for effect in effects:
                self.assertEqual(effect.adjudication_id, "")


class CommittedGovernanceTest(unittest.TestCase):
    """The committed ledger, policy and audit."""

    def test_the_committed_ledger_holds_no_synthetic_or_real_approval(self) -> None:
        ledger = adjudication.load_adjudications(ROOT)
        self.assertIsNotNone(ledger)
        for entry in ledger.values():
            with self.subTest(adjudication=entry.adjudication_id):
                self.assertNotIn(
                    "synthetic_fixture", (entry.effect_evidence, entry.system_match)
                )
                self.assertFalse(entry.intervention_id.startswith("synthetic_"))
                self.assertFalse(entry.basis_record.startswith("tests/"))
        # O8b approves no real compound: a later approval is a decision of its own.
        self.assertEqual(ledger, {})

    def test_every_role_of_the_library_versions_is_listed(self) -> None:
        """Unlisted roles are refused anyway; listing them all keeps the refusal
        a recorded decision rather than a default."""
        policy = adjudication.load_target_policy(ROOT)
        for version in (V052, V060):
            path = ROOT / "models/superset" / version / "node_dictionary.tsv"
            with path.open(encoding="utf-8", newline="") as handle:
                roles = {
                    row["model_role"] for row in csv.DictReader(handle, delimiter="\t")
                }
            with self.subTest(version=version):
                self.assertEqual(roles - set(policy.roles), set())

    def test_every_policy_basis_exists(self) -> None:
        adjudication.check_policy_basis(ROOT)

    def test_the_committed_audit_is_current(self) -> None:
        self.assertEqual(
            (ROOT / AUDIT_PATH).read_text(encoding="utf-8"),
            render_audit(target_audit(V060, ROOT)),
        )

    def test_the_v060_direct_target_set(self) -> None:
        """Pinned so that a policy edit that changes it is a visible decision."""
        eligible = {
            r["node_id"]
            for r in target_audit(V060, ROOT)
            if r["direct_target"] == "yes"
        }
        self.assertEqual(
            eligible,
            {
                "E_PGR",
                "E_IHH",
                "E_LIF",
                "E_GP130_STAT3",
                "E_PODXL",
                "E_PC6",
                "E_HBEGF",
                "E_SPP1_EXPR",
                "E_ITGAVB3_5",
                "E_CD98_CD9",
                "E_ANXA2_ACTIN",
                "E_CDH1_APICAL",
                "S_PGR",
                "S_PKA",
                "S_NR2F2",
                "S_HAND2",
                "S_SPP1",
                "S_TAZ_ECM",
                "X_SPP1_LUMEN_FREE",
            },
        )

    def test_no_derived_node_is_a_direct_target(self) -> None:
        refused_roles = {
            "phenotype",
            "readout",
            "state",
            "latent_state",
            "interface_route",
            "structural_uncertainty",
            "regulator_or_readout",
            "anti_receptive_state",
            "paracrine_inhibitor_of_receptivity",
        }
        for row in target_audit(V060, ROOT):
            if row["model_role"] in refused_roles:
                with self.subTest(node=row["node_id"]):
                    self.assertEqual(row["direct_target"], "no")


if __name__ == "__main__":
    unittest.main()
