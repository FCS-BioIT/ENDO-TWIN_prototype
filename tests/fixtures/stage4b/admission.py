"""Synthetic compounds for gate G13 (``docs/stage4b_direct_admission.md`` §7).

``Compound`` builds the four parts a direct intervention's admission appends --
its evidence-register rows, its target declaration, one approval per effect and
its library rows -- with every digest bound: each approval's
``library_row_sha256``, the declaration's ``library_rows_sha256`` and generated
``construction_overlap``, and each approval's ``target_declaration_sha256``. A
test that breaks one rule overrides one field, and every other binding still
holds, so the refusal it sees is the rule under test and not a stale digest.

Nothing here is evidence or a reagent. Every compound is appended to a sandbox
built by ``tests/fixtures/o8_markerless/sandbox.py``; the committed library,
ledger, declarations and register are never touched. Evidence rows default to
the ``synthetic_fixture`` status, which the loader accepts only with synthetic
approvals. ``real_shape=True`` gives sandbox-only rows a non-synthetic status, so
a test can exercise the rules a real approval meets (``system_grade``); those
rows say in every field that they are not evidence.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from dt_adoc.perturbations.adjudication import (
    ADJUDICATION_COLUMNS,
    COMPARTMENTS,
    DECLARATION_COLUMNS,
    _sha256,
    construction_overlap,
    library_row_digest,
    library_rows_digest,
)
from dt_adoc.perturbations.engine import LIBRARY_COLUMNS, InterventionEffect

FIXTURE = Path(__file__).resolve().parent
V060 = "adoc-literature-superset-v0.6.0"
README = "tests/fixtures/stage4b/README.md"
SYNTHETIC = "synthetic_fixture"
APPROVED = "approved_for_model_execution"
REGISTER_COLUMNS = (
    "evidence_id",
    "source_file",
    "location",
    "system",
    "condition",
    "observation",
    "model_role",
    "planned_use",
    "evidence_level",
    "status",
    "notes",
)


def _effect(values: dict[str, str]) -> InterventionEffect:
    parsed: dict[str, object] = dict(values)
    for column in ("legacy_perturbation_ids", "abstraction_sources", "evidence_ids"):
        parsed[column] = tuple(p for p in values[column].split(";") if p)
    return InterventionEffect(**parsed)


@dataclass
class Compound:
    name: str
    targets: tuple[str, ...]
    known: tuple[str, ...]
    reached: tuple[str, ...] = COMPARTMENTS
    unrepresented: str = ""
    declaration_id: str = "DTD-900"
    model_version: str = V060
    #: Two ids when ``real_shape``: the qualifying E2 measurement and a line.
    real_shape: bool = False
    system_grade: str = SYNTHETIC
    library: dict[str, str] = field(default_factory=dict)
    declaration: dict[str, str] = field(default_factory=dict)
    approval: dict[str, str] = field(default_factory=dict)

    @property
    def evidence_ids(self) -> tuple[str, ...]:
        tag = self.name.upper()
        if self.real_shape:
            return (f"G13-TEST-{tag}-PRIMARY", f"G13-TEST-{tag}-LINE")
        return (f"SYNTHETIC-G13-{tag}",)

    def evidence_rows(self) -> list[str]:
        rows = []
        for evidence_id in self.evidence_ids:
            row = {
                "evidence_id": evidence_id,
                "source_file": README,
                "location": self.name,
                "system": "none",
                "condition": "none",
                "observation": "No observation: G13 sandbox fixture",
                "model_role": "none",
                "planned_use": "test fixture only",
                "evidence_level": "none",
                "status": "g13_test_only" if self.real_shape else SYNTHETIC,
                "notes": "Not evidence. Sandbox-only; never committed to the register.",
            }
            rows.append("\t".join(row[c] for c in REGISTER_COLUMNS))
        return rows

    def library_values(self) -> list[dict[str, str]]:
        values = []
        for target in self.targets:
            row = {
                "intervention_id": self.name,
                "intervention_label": f"G13 fixture {self.name}",
                "intervention_class": SYNTHETIC,
                "model_version": self.model_version,
                "legacy_input_node": "",
                "legacy_perturbation_ids": "",
                "target_node": target,
                "mode": "activity_veto",
                "mapping_basis": "direct_supported_effect",
                "model_abstraction": f"Fixture: a full activity veto of {';'.join(self.targets)}",
                "abstraction_sources": README,
                "evidence_ids": ";".join(self.evidence_ids),
                "claim_boundary": "Test fixture only. Not evidence and not a claim about any reagent.",
                **self.library,
            }
            values.append(row)
        return values

    def parts(self, root: Path) -> dict[str, list[str]]:
        """``{part: rows}`` in the sandbox's part names, every digest bound."""
        library = self.library_values()
        effects = [_effect(row) for row in library]
        declaration = {
            "declaration_id": self.declaration_id,
            "intervention_id": self.name,
            "model_version": self.model_version,
            "agent_class": "small_molecule",
            "agent_specification": "none: G13 fixture, not a reagent",
            "reached_compartments": ";".join(self.reached),
            "known_target_entities": ";".join(self.known),
            "declared_targets": ";".join(self.targets),
            "unrepresented_known_targets": self.unrepresented,
            "target_profile_sources": README,
            "profile_searched_on": "2026-10-04",
            "construction_overlap": construction_overlap(
                self.model_version, set(self.targets), set(self.evidence_ids), root
            ),
            "library_rows_sha256": library_rows_digest(effects),
            "adjudicator": "G13 fixture",
            "dated": "2026-10-04",
            **self.declaration,
        }
        declaration_line = "\t".join(declaration[c] for c in DECLARATION_COLUMNS)
        real = self.real_shape
        approvals = []
        for index, effect in enumerate(effects, start=1):
            approval = {
                "adjudication_id": f"G13-{self.name.upper()}-{index}",
                "intervention_id": self.name,
                "model_version": self.model_version,
                "target_node": effect.target_node,
                "mode": "activity_veto",
                "decision": APPROVED,
                "evidence_ids": ";".join(self.evidence_ids),
                "effect_evidence": "target_activity_reduced" if real else SYNTHETIC,
                "system_match": "matches_model_compartment" if real else SYNTHETIC,
                "biological_system": "none: G13 fixture",
                "library_row_sha256": library_row_digest(effect),
                "basis_record": README,
                "rationale": "Fixture approval so a test can license a fixture row.",
                "adjudicator": "G13 fixture",
                "dated": "2026-10-04",
                "system_grade": self.system_grade,
                "target_declaration_sha256": _sha256(declaration_line),
                **self.approval,
            }
            approvals.append("\t".join(approval[c] for c in ADJUDICATION_COLUMNS))
        return {
            "evidence": self.evidence_rows(),
            "declaration": [declaration_line],
            "adjudication": approvals,
            "library": ["\t".join(row[c] for c in LIBRARY_COLUMNS) for row in library],
        }


def add(sandbox, root: Path, compound: Compound, parts: tuple[str, ...] = ()) -> None:
    """Append ``compound``'s ``parts`` (all four by default) to a sandbox.

    Appending library rows regenerates the expressivity artefacts, as
    ``sandbox.add_compound`` does for the O8 fixtures.
    """
    if not (root / README).is_file():
        (root / README).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(FIXTURE / "README.md", root / README)
    built = compound.parts(root)
    for part in parts or tuple(sandbox.PARTS):
        with (root / sandbox.PARTS[part]).open("a", encoding="utf-8") as handle:
            handle.write("".join(row + "\n" for row in built[part]))
    if "library" in (parts or tuple(sandbox.PARTS)):
        sandbox.regenerate_expressivity(root)
