"""C2 -- which tissue compartment an outlet measurement can be attributed to.

The 163-paper re-audit (``SRC-006`` section 4.1, C2) asks for the observation
model to be corrected before more biology is added: PRL is a stromal readout,
IGFBP-1 is compartment-ambiguous between epithelium and stroma, PAEP is a
glandular/global secretory readout, and an SPP1 outlet would read a mixed free
ligand pool. ``context/observation_compartment_attribution.tsv`` records those
statements. This module loads that table, validates it against the observation
map, and renders the interpretation it licenses.

It is an overlay on the observation map, not an edit to it, and it changes no
calculation:

* ``config/observation_model_map.tsv`` is frozen by the closed Phase 1B and U8
  units, which pin its sha256. It is read here and never written.
* No activation status, weight, objective, comparison, model node or rule is
  derived from the overlay. OM-002 stays an ``active_diagnostic`` on
  ``S_IGFBP1``, evaluated exactly as before; C2 changes what the measured
  IGFBP-1 is said to represent, not the non-inversion check.
* ``dt_adoc.calibration.observation_map`` does not read the overlay, so no
  closed unit sees it. ``tests/unit/test_compartment_attribution.py`` holds
  that isolation in place.
* Current consumers of the evaluation carry the interpretation, and the one
  such consumer today is ``dt_adoc evaluate-constraints``. Each check is passed
  through ``annotate_check``, which attaches the mapping's attribution (OM-002:
  CA-002, ``epithelial_and_stromal_ambiguous``, with S_IGFBP1 as the
  computational proxy) and changes no number. ``describe_check`` refuses to
  word an ambiguous measurement as stromal-specific evidence. This is the
  owner's 2026-09-29 SEMANTIC_OR_PROTOCOL decision; the numerical diagnostic
  and the frozen map are unchanged.

The table lives under ``context/`` rather than ``config/``: the closed Phase 2B
audit counts every new file under ``config/`` as an unapproved change to a
frozen artifact, so a new config file would stop the closed phases replaying.

Every artifact that consumes the overlay records its sha256 (``build``, and
``annotated_checks_payload`` for the evaluator's output).
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dt_adoc.calibration.observation_map import load_observation_map
from dt_adoc.model.provenance import repo_root

ATTRIBUTION_PATH = Path("context/observation_compartment_attribution.tsv")
OBSERVATION_MAP_PATH = Path("config/observation_model_map.tsv")
OUT_DIR = Path("docs/c2_observation_compartments")
REPORT = OUT_DIR / "attribution_report.md"
SUMMARY = OUT_DIR / "attribution_summary.json"
OUTPUTS = (REPORT, SUMMARY)

ATTRIBUTION_VERSION = "C2-v1"

#: The observation map's sha256 as frozen by the closed Phase 1B unit
#: (tests/unit/test_phase1b_closure.py). The summary records whether the map
#: read is still those bytes, rather than asserting it.
PHASE1B_FROZEN_MAP_SHA256 = "74f0d5d0896beba57a0a03960239ad2fc039f315fa42a2209a65e228bfa3aff5"

ATTRIBUTION_COLUMNS: tuple[str, ...] = (
    "attribution_id",
    "attribution_version",
    "mapping_ids",
    "analyte",
    "outlet",
    "compartment_attribution",
    "model_interpretation",
    "prohibited_interpretation",
    "supersedes_in_rendering",
    "evidence_ids",
    "verification",
)

COMPARTMENT_ATTRIBUTIONS: frozenset[str] = frozenset(
    {
        "stromal_attributed",
        "epithelial_and_stromal_ambiguous",
        "secretory_epithelial_compartment_uncertain",
        "mixed_source_free_ligand_pool",
    }
)

#: An analyte with no registered outlet measurement. Such a row carries no
#: mapping_ids, and it may exist only while no map row names its analyte.
OUTLET_NOT_REGISTERED = "not_registered"

#: Map rows that are not outlet measurements of a single named analyte: marker
#: composites (OM-009, OM-010), and records that carry no measured row at all
#: (``source_rows_n == 0``: the protocol-coverage gap OM-011 and the XAV939
#: record OM-017). There is nothing for a compartment attribution to qualify.
COMPOSITE_PREFIX = "multi_analyte_composite:"

#: Where each evidence-id family resolves.
EVIDENCE_REGISTRIES: dict[str, tuple[Path, str]] = {
    "SOFIA-": (Path("context/evidence-register.tsv"), "evidence_id"),
    "REF-": (Path("context/literature/references.tsv"), "ref_id"),
    "SRC-": (Path("context/literature/source-provenance.tsv"), "source_id"),
}


class AttributionError(ValueError):
    """The attribution table is malformed or disagrees with the observation map."""


@dataclass(frozen=True)
class Attribution:
    attribution_id: str
    mapping_ids: tuple[str, ...]
    analyte: str
    outlets: tuple[str, ...]
    compartment_attribution: str
    model_interpretation: str
    prohibited_interpretation: str
    supersedes_in_rendering: str
    evidence_ids: tuple[str, ...]
    verification: str


def _split(value: str) -> tuple[str, ...]:
    return tuple(part for part in value.split(";") if part)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or ()), list(reader)


def map_analytes(row: dict[str, str]) -> tuple[str, ...]:
    """The single analytes a map row measures; () for composites and records."""
    protein = row["protein"]
    if (
        protein.startswith(COMPOSITE_PREFIX)
        or protein == "not_applicable"
        or int(row["source_rows_n"] or 0) == 0
    ):
        return ()
    return _split(protein)


def _known_evidence_ids(root: Path) -> set[str]:
    known: set[str] = set()
    for path, column in EVIDENCE_REGISTRIES.values():
        known |= {row[column] for row in _read_tsv(root / path)[1]}
    return known


def validate(
    rows: list[dict[str, str]],
    map_rows: list[dict[str, str]],
    known_evidence: set[str],
) -> list[str]:
    """Every problem with the table, as messages; [] when it is valid."""
    problems: list[str] = []
    by_mapping = {row["mapping_id"]: row for row in map_rows}
    seen_ids: set[str] = set()
    covered: dict[tuple[str, str], list[str]] = {}
    for row in rows:
        rid = row["attribution_id"]
        if rid in seen_ids:
            problems.append(f"{rid}: duplicate attribution_id")
        seen_ids.add(rid)
        if row["attribution_version"] != ATTRIBUTION_VERSION:
            problems.append(f"{rid}: attribution_version is not {ATTRIBUTION_VERSION}")
        if row["compartment_attribution"] not in COMPARTMENT_ATTRIBUTIONS:
            problems.append(f"{rid}: unknown compartment_attribution")
        for column in ("model_interpretation", "prohibited_interpretation", "verification"):
            if not row[column].strip():
                problems.append(f"{rid}: {column} is empty")
        evidence = _split(row["evidence_ids"])
        if not evidence:
            problems.append(f"{rid}: no evidence_ids")
        for eid in evidence:
            if not eid.startswith(tuple(EVIDENCE_REGISTRIES)):
                problems.append(f"{rid}: {eid} has no registry")
            elif eid not in known_evidence:
                problems.append(f"{rid}: {eid} does not resolve")
        analyte = row["analyte"]
        mapping_ids = _split(row["mapping_ids"])
        outlets = _split(row["outlet"])
        if not mapping_ids:
            if outlets != (OUTLET_NOT_REGISTERED,):
                problems.append(f"{rid}: an analyte-level row must have outlet {OUTLET_NOT_REGISTERED}")
            if any(analyte in map_analytes(m) for m in map_rows):
                problems.append(f"{rid}: {analyte} has map rows, so the row must name them")
        for mid in mapping_ids:
            mapped = by_mapping.get(mid)
            if mapped is None:
                problems.append(f"{rid}: {mid} is not in the observation map")
                continue
            if analyte not in map_analytes(mapped):
                problems.append(f"{rid}: {mid} does not measure {analyte}")
            if mapped["outlet"] not in (*outlets, "", "not_applicable"):
                problems.append(f"{rid}: {mid} outlet {mapped['outlet']} is not declared")
            covered.setdefault((mid, analyte), []).append(rid)
        phrase = row["supersedes_in_rendering"]
        if phrase and not any(phrase in by_mapping[m]["comparison"] for m in mapping_ids if m in by_mapping):
            problems.append(f"{rid}: superseded phrase is not in any named row's comparison")
    attributed = {row["analyte"] for row in rows}
    for mapped in map_rows:
        for analyte in map_analytes(mapped):
            if analyte not in attributed:
                continue
            claims = covered.get((mapped["mapping_id"], analyte), [])
            if len(claims) != 1:
                problems.append(
                    f"{mapped['mapping_id']}/{analyte}: attributed by {len(claims)} rows, not exactly one"
                )
    return problems


def load_attributions(root: Path | None = None) -> tuple[Attribution, ...]:
    """The validated table. Raises AttributionError on any problem."""
    root = root or repo_root()
    header, rows = _read_tsv(root / ATTRIBUTION_PATH)
    if tuple(header) != ATTRIBUTION_COLUMNS:
        raise AttributionError(f"columns are {header}, expected {list(ATTRIBUTION_COLUMNS)}")
    problems = validate(rows, load_observation_map(root), _known_evidence_ids(root))
    if problems:
        raise AttributionError("; ".join(problems))
    return tuple(
        Attribution(
            attribution_id=row["attribution_id"],
            mapping_ids=_split(row["mapping_ids"]),
            analyte=row["analyte"],
            outlets=_split(row["outlet"]),
            compartment_attribution=row["compartment_attribution"],
            model_interpretation=row["model_interpretation"],
            prohibited_interpretation=row["prohibited_interpretation"],
            supersedes_in_rendering=row["supersedes_in_rendering"],
            evidence_ids=_split(row["evidence_ids"]),
            verification=row["verification"],
        )
        for row in rows
    )


def rendered_comparison(comparison: str, attribution: Attribution) -> str:
    """The map row's comparison text with any superseded phrase marked, not deleted."""
    phrase = attribution.supersedes_in_rendering
    if not phrase or phrase not in comparison:
        return comparison
    marker = f"[superseded by {attribution.attribution_id}: \"{phrase}\" -- {attribution.compartment_attribution}]"
    return comparison.replace(phrase, marker)


def interpretation_rows(root: Path | None = None) -> list[dict[str, str]]:
    """One row per attributed (mapping, analyte), plus analyte-level rows.

    The map columns are copied unchanged; only the interpretation is added.
    """
    root = root or repo_root()
    attributions = load_attributions(root)
    by_mapping = {row["mapping_id"]: row for row in load_observation_map(root)}
    rows: list[dict[str, str]] = []
    for attribution in attributions:
        base = {
            "attribution_id": attribution.attribution_id,
            "analyte": attribution.analyte,
            "compartment_attribution": attribution.compartment_attribution,
            "model_interpretation": attribution.model_interpretation,
            "prohibited_interpretation": attribution.prohibited_interpretation,
        }
        if not attribution.mapping_ids:
            rows.append({**base, "mapping_id": "", "outlet": OUTLET_NOT_REGISTERED,
                         "model_nodes": "", "activation_status": "", "comparison": ""})
        for mid in attribution.mapping_ids:
            mapped = by_mapping[mid]
            rows.append({
                **base,
                "mapping_id": mid,
                "outlet": mapped["outlet"],
                "model_nodes": mapped["model_nodes"],
                "activation_status": mapped["activation_status"],
                "comparison": rendered_comparison(mapped["comparison"], attribution),
            })
    return rows


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_report(root: Path, summary: dict[str, Any]) -> str:
    attributions = load_attributions(root)
    lines = [
        "# C2 -- observation compartment attribution",
        "",
        "Generated by `pixi run build-c2-attribution` from",
        f"`{ATTRIBUTION_PATH.as_posix()}` ({ATTRIBUTION_VERSION}) and the frozen",
        f"`{OBSERVATION_MAP_PATH.as_posix()}`; input hashes are in",
        f"`{SUMMARY.as_posix()}`. Do not edit by hand.",
        "",
        "This is an interpretation overlay only. The observation map is not",
        "edited, and no activation status, weight, objective, comparison, model",
        "node or rule changes. OM-002 remains an `active_diagnostic` on",
        "`S_IGFBP1` with the same non-inversion calculation.",
        "",
        "## Attributions",
        "",
    ]
    for a in attributions:
        lines += [
            f"### {a.attribution_id} -- {a.analyte} ({a.compartment_attribution})",
            "",
            f"- **Map rows:** {', '.join(a.mapping_ids) or 'none (no outlet measurement registered)'}",
            f"- **Model interpretation:** {a.model_interpretation}",
            f"- **Prohibited interpretation:** {a.prohibited_interpretation}",
            f"- **Evidence:** {', '.join(a.evidence_ids)}",
            f"- **Verification:** {a.verification}",
        ]
        if a.supersedes_in_rendering:
            lines.append(
                f"- **Supersedes in rendering:** \"{a.supersedes_in_rendering}\" "
                "(the frozen map row keeps its text)"
            )
        lines.append("")
    lines += [
        "## Map rows as interpreted",
        "",
        "| mapping | analyte | outlet | model nodes | activation status | attribution | comparison (rendered) |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in interpretation_rows(root):
        lines.append(
            f"| {row['mapping_id'] or '--'} | {row['analyte']} | {row['outlet'] or '--'} | "
            f"{row['model_nodes'] or '--'} | {row['activation_status'] or '--'} | "
            f"{row['attribution_id']} | {_cell(row['comparison']) or '--'} |"
        )
    lines += [
        "",
        f"Map rows attributed: {summary['attributed_map_rows']}. Not attributed, because",
        "they are no outlet measurement of a single analyte (a marker composite, or a",
        f"record with zero source rows): {', '.join(sorted(set(summary['unattributed_map_rows']) - set(summary['unattributed_measured_rows'])))}.",
        ("Measured single-analyte rows of an analyte this table does not cover: "
         f"{', '.join(summary['unattributed_measured_rows']) or 'none'}."),
        "",
    ]
    return "\n".join(lines)


def compute_summary(root: Path) -> dict[str, Any]:
    attributions = load_attributions(root)
    map_rows = load_observation_map(root)
    attributed = sorted({m for a in attributions for m in a.mapping_ids})
    return {
        "unit": "C2 observation compartment attribution",
        "attribution_version": ATTRIBUTION_VERSION,
        "inputs_sha256": {
            ATTRIBUTION_PATH.as_posix(): _sha(root / ATTRIBUTION_PATH),
            OBSERVATION_MAP_PATH.as_posix(): _sha(root / OBSERVATION_MAP_PATH),
            "src/dt_adoc/observations/compartment_attribution.py": _sha(Path(__file__)),
            **{path.as_posix(): _sha(root / path) for path, _ in EVIDENCE_REGISTRIES.values()},
        },
        "attributions": {
            a.attribution_id: {
                "analyte": a.analyte,
                "compartment_attribution": a.compartment_attribution,
                "mapping_ids": list(a.mapping_ids),
            }
            for a in attributions
        },
        "attributed_map_rows": len(attributed),
        "unattributed_map_rows": sorted(
            row["mapping_id"] for row in map_rows if row["mapping_id"] not in attributed
        ),
        # Measured single-analyte rows of an analyte the table does not cover.
        # The report's reason for leaving rows out applies only while this is empty.
        "unattributed_measured_rows": sorted(
            row["mapping_id"]
            for row in map_rows
            if row["mapping_id"] not in attributed and map_analytes(row)
        ),
        "observation_map_is_phase1b_frozen_bytes": _sha(root / OBSERVATION_MAP_PATH)
        == PHASE1B_FROZEN_MAP_SHA256,
        "changes_to_activation_weight_objective_or_model": "none",
    }


def render_outputs(root: Path | None = None) -> dict[Path, str]:
    """Every output's exact text, computed without writing anything."""
    root = root or repo_root()
    summary = compute_summary(root)
    return {
        SUMMARY: json.dumps(summary, indent=2, sort_keys=True) + "\n",
        REPORT: render_report(root, summary),
    }


def build(root: Path | None = None) -> None:
    root = root or repo_root()
    outputs = render_outputs(root)
    (root / OUT_DIR).mkdir(parents=True, exist_ok=True)
    for relative, text in outputs.items():
        (root / relative).write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# The active interpretation path (owner decision 2026-09-29, recorded as
# SEMANTIC_OR_PROTOCOL): current consumers of the observation-map evaluation
# carry the C2 attribution of each checked mapping. The numerical diagnostic is
# untouched: ``evaluate_directional_constraints`` still reads only the frozen
# map, and every ConstraintCheck field is passed through unchanged. Closed units
# and historical builders never call these functions.

#: Wording that would present an outlet measurement as specific to the stromal
#: compartment or to a stromal model state.
_STROMAL_SPECIFIC = re.compile(
    r"strom\w*[- ]specific|specific (?:to|for) (?:the )?strom|exclusively strom|"
    r"purely strom|strom\w* only\b|only strom",
    re.IGNORECASE,
)
#: Attributions under which stromal-specific wording is refused.
NOT_STROMAL_SPECIFIC = frozenset({
    "epithelial_and_stromal_ambiguous",
    "secretory_epithelial_compartment_uncertain",
    "mixed_source_free_ligand_pool",
})


class InterpretationRefused(ValueError):
    """A statement contradicts the C2 attribution of the measurement it describes."""


def attribution_by_mapping(root: Path | None = None) -> dict[tuple[str, str], Attribution]:
    """(mapping_id, analyte) -> its attribution, for every attributed map row."""
    return {(m, a.analyte): a for a in load_attributions(root) for m in a.mapping_ids}


def _attribution_for(mapping_id: str, root: Path | None) -> Attribution | None:
    matches = {a.attribution_id: a for (m, _), a in attribution_by_mapping(root).items()
               if m == mapping_id}
    if len(matches) > 1:
        raise AttributionError(f"{mapping_id} has more than one attribution: {sorted(matches)}")
    return next(iter(matches.values()), None)


def check_statement(annotated: dict[str, Any], statement: str) -> str:
    """Refuse a statement that calls an ambiguous measurement stromal-specific."""
    if (annotated.get("compartment_attribution") in NOT_STROMAL_SPECIFIC
            and _STROMAL_SPECIFIC.search(statement)):
        raise InterpretationRefused(
            f"{annotated['mapping_id']} is {annotated['compartment_attribution']} "
            f"({annotated['attribution_id']}); it may not be described as stromal-specific "
            f"evidence: {statement!r}"
        )
    return statement


def annotate_check(check: Any, root: Path | None = None) -> dict[str, Any]:
    """A ConstraintCheck with its numbers unchanged and its C2 attribution attached."""
    annotated = {
        "mapping_id": check.mapping_id,
        "activation_status": check.activation_status,
        "model_node": check.model_node,
        "protocol_high": check.protocol_high,
        "protocol_low": check.protocol_low,
        "value_high": check.value_high,
        "value_low": check.value_low,
        "satisfied": check.satisfied,
        "excludes_candidate": check.excludes_candidate,
    }
    attribution = _attribution_for(check.mapping_id, root)
    annotated.update({
        "attribution_id": attribution.attribution_id if attribution else "",
        "compartment_attribution": attribution.compartment_attribution if attribution else "",
        "model_interpretation": attribution.model_interpretation if attribution else "",
        "prohibited_interpretation": attribution.prohibited_interpretation if attribution else "",
    })
    return annotated


def describe_check(annotated: dict[str, Any]) -> str:
    """The one-line interpretation a current consumer may print for a check."""
    role = ("feasibility gate" if annotated["activation_status"] == "active_constraint"
            else "non-inversion diagnostic, never excludes a candidate")
    verdict = "satisfied" if annotated["satisfied"] else "violated"
    text = (f"{annotated['mapping_id']} ({role}) on computational proxy "
            f"{annotated['model_node']}: {verdict}")
    if annotated["attribution_id"]:
        text += (f"; measured outlet is {annotated['compartment_attribution']} "
                 f"({annotated['attribution_id']})")
    return check_statement(annotated, text)


def annotated_checks_payload(checks: list[Any], root: Path | None = None) -> dict[str, Any]:
    """Annotated checks plus the overlay's provenance (the C2 hashing contract)."""
    root = root or repo_root()
    return {
        "checks": [annotate_check(c, root) for c in checks],
        "observation_compartment_attribution": {
            "path": ATTRIBUTION_PATH.as_posix(),
            "sha256": _sha(root / ATTRIBUTION_PATH),
            "attribution_version": ATTRIBUTION_VERSION,
        },
    }


if __name__ == "__main__":
    build()
