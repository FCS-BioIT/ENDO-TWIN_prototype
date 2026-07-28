"""Citation-integrity checks for the DT_ADOC bibliography.

The model's credibility rests on `context/literature/references.tsv`. These
checks answer three separate questions that are easy to conflate:

1. Is the bibliography internally well formed (schema, duplicate identifiers)?
2. Does every cited identifier resolve to a real published record?
3. Does every evidence id used by a node or edge trace to that bibliography?

Only (2) needs the network. Its results are cached in a verification table so
the test suite can assert citation integrity offline and so a reviewer can see
exactly what was checked and when, rather than trusting that someone once ran it.

Resolving a DOI proves the paper exists. It does **not** prove the paper supports
the edge direction, compartment or species encoded in the model. That judgement
is recorded per relation in the evidence tables and is not automatable.
"""

from __future__ import annotations

import csv
import difflib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

REFERENCES_PATH = Path("context/literature/references.tsv")
VERIFICATION_PATH = Path("context/literature/citation_verification.tsv")

REQUIRED_REFERENCE_COLUMNS = (
    "ref_id",
    "first_author",
    "year",
    "title",
    "journal",
    "species",
    "study_type",
    "doi",
    "evidence_level",
    "compartment",
    "key_use",
    "url",
)

VERIFICATION_COLUMNS = (
    "ref_id",
    "doi",
    "resolver",
    "resolved",
    "title_similarity",
    "year_matches",
    "resolved_title",
    "checked_on",
    "note",
)

#: Below this the stored title and the resolver title are treated as different
#: works rather than as an abbreviation of the same one.
TITLE_SIMILARITY_FLOOR = 0.65


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _norm(text: str) -> str:
    return "".join(c for c in text.lower() if c.isalnum() or c == " ").strip()


@dataclass
class CitationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "citations_intact" if not self.errors else "citation_defects"

    def payload(self) -> dict[str, object]:
        return {
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
            "checks": self.checks,
        }


def load_references(root: Path | None = None) -> list[dict[str, str]]:
    path = (root or repo_root()) / REFERENCES_PATH
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def load_verification(root: Path | None = None) -> list[dict[str, str]]:
    path = (root or repo_root()) / VERIFICATION_PATH
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def resolve_doi(doi: str, *, timeout: int = 25) -> dict[str, object] | None:
    """Resolve a DOI against Crossref. Returns None if it does not resolve."""
    request = urllib.request.Request(
        f"https://api.crossref.org/works/{doi}",
        headers={"User-Agent": "DT_ADOC-citation-audit/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)["message"]
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
        # A DOI that does not resolve is a finding, not a crash. Narrow the
        # catch so a genuine programming error still surfaces.
        return None


def check_bibliography(root: Path | None = None) -> CitationReport:
    """Offline structural and cross-reference integrity of the bibliography."""
    active_root = root or repo_root()
    report = CitationReport()
    references = load_references(active_root)

    if not references:
        report.errors.append("bibliography is empty")
        return report

    missing = [c for c in REQUIRED_REFERENCE_COLUMNS if c not in references[0]]
    if missing:
        report.errors.append(f"bibliography missing columns: {missing}")
    report.checks.append("reference_schema")

    # Duplicate identifiers silently inflate apparent evidence breadth.
    for field_name in ("ref_id", "doi"):
        seen: dict[str, str] = {}
        for row in references:
            value = row.get(field_name, "").strip().lower()
            if not value:
                continue
            if value in seen:
                report.errors.append(
                    f"duplicate {field_name} {value!r} in {seen[value]} and {row['ref_id']}"
                )
            seen[value] = row["ref_id"]
    pmids = [r.get("pmid", "").strip() for r in references if r.get("pmid", "").strip()]
    if len(pmids) != len(set(pmids)):
        report.errors.append("duplicate pmid values in bibliography")
    report.checks.append("identifier_deduplication")

    for row in references:
        if not row.get("doi", "").strip():
            report.errors.append(f"{row['ref_id']} has no DOI")
        elif not row["doi"].strip().startswith("10."):
            report.errors.append(
                f"{row['ref_id']} DOI is not well formed: {row['doi']!r}"
            )
    report.checks.append("doi_present_and_well_formed")

    # Every evidence id used by the model must reach the bibliography.
    register_path = active_root / "context" / "evidence-register.tsv"
    if register_path.exists():
        with register_path.open(encoding="utf-8") as handle:
            register = {
                r["evidence_id"]: r for r in csv.DictReader(handle, delimiter="\t")
            }
        known_refs = {r["ref_id"] for r in references}
        for evidence_id, row in register.items():
            for ref_id in filter(None, (x.strip() for x in row["location"].split(";"))):
                if ref_id.startswith("REF-") and ref_id not in known_refs:
                    report.errors.append(
                        f"evidence {evidence_id} cites unknown reference {ref_id}"
                    )
        report.checks.append("evidence_ids_reach_bibliography")

    return report


def check_resolution_cache(root: Path | None = None) -> CitationReport:
    """Assert every reference has a recorded, successful resolution."""
    active_root = root or repo_root()
    report = CitationReport()
    references = load_references(active_root)
    verification = {r["ref_id"]: r for r in load_verification(active_root)}

    if not verification:
        report.errors.append(
            f"no citation verification cache at {VERIFICATION_PATH}; "
            "run `pixi run verify-citations`"
        )
        return report

    for row in references:
        record = verification.get(row["ref_id"])
        if record is None:
            report.errors.append(f"{row['ref_id']} has no verification record")
            continue
        if record["resolved"].strip().lower() != "true":
            report.errors.append(
                f"{row['ref_id']} DOI {row['doi']} did not resolve: {record['note']}"
            )
            continue
        if float(record["title_similarity"]) < TITLE_SIMILARITY_FLOOR:
            report.warnings.append(
                f"{row['ref_id']} stored title differs from the resolved record "
                f"(similarity {record['title_similarity']}); "
                f"resolved: {record['resolved_title'][:70]}"
            )
        if record["year_matches"].strip().lower() != "true":
            report.errors.append(
                f"{row['ref_id']} year disagrees with the resolved record"
            )
    report.checks.append("every_reference_resolved")
    return report


def verify_and_write_cache(
    root: Path | None = None, *, checked_on: str = ""
) -> list[dict[str, str]]:
    """Resolve every DOI online and write the verification cache. Needs network."""
    active_root = root or repo_root()
    rows: list[dict[str, str]] = []
    for reference in load_references(active_root):
        doi = reference["doi"].strip()
        message = resolve_doi(doi)
        if message is None:
            rows.append(
                {
                    "ref_id": reference["ref_id"],
                    "doi": doi,
                    "resolver": "crossref",
                    "resolved": "false",
                    "title_similarity": "0.0",
                    "year_matches": "false",
                    "resolved_title": "",
                    "checked_on": checked_on,
                    "note": "DOI did not resolve",
                }
            )
            continue
        resolved_title = (message.get("title") or [""])[0]
        parts = message.get("issued", {}).get("date-parts") or [[None]]
        resolved_year = parts[0][0]
        similarity = difflib.SequenceMatcher(
            None, _norm(resolved_title)[:80], _norm(reference["title"])[:80]
        ).ratio()
        year_matches = (
            resolved_year is not None
            and abs(int(resolved_year) - int(reference["year"])) <= 1
        )
        rows.append(
            {
                "ref_id": reference["ref_id"],
                "doi": doi,
                "resolver": "crossref",
                "resolved": "true",
                "title_similarity": f"{similarity:.2f}",
                "year_matches": "true" if year_matches else "false",
                "resolved_title": resolved_title,
                "checked_on": checked_on,
                "note": ""
                if similarity >= TITLE_SIMILARITY_FLOOR
                else "stored title is abbreviated or differs",
            }
        )
    path = active_root / VERIFICATION_PATH
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(VERIFICATION_COLUMNS), delimiter="\t"
        )
        writer.writeheader()
        writer.writerows(rows)
    return rows
