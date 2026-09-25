"""Phase 2B: metadata-only candidate inventory, qualification and selection.

The inventory (`docs/phase2b/candidate_inventory.tsv`) is hand-curated from
titles, methods, data-availability statements, accession pages and sample
metadata. It may carry NO expression value: its columns are a closed set, no
column may name an expression, detection, threshold, rank or outcome quantity,
and no cell may mention KLF12. `validate_inventory` enforces this.

`qualify` applies the owner decisions of 2026-09-25 (D1, D2, D5, D7, D8) to
the inventory mechanically. It reads metadata only and cannot see a KLF12
value, a model output or an ADOC outcome. `select` orders the qualified
candidates by the frozen D7 hierarchy. Only the first one proceeds to value
analysis. A value-blind failure after selection (for example, pipeline
reproduction) passes to the next candidate. A value-aware failure (no stable
separation) never does: that would be choosing a reference by its KLF12
distribution.
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from dt_adoc.personalization.phase2b.identity import (
    ascii_form,
    names_adoc_accession,
    names_adoc_donor,
)

INVENTORY = Path("docs/phase2b/candidate_inventory.tsv")

INVENTORY_COLUMNS = (
    "candidate_id",
    "citation",
    "accessions",
    "system",
    "protocol_detail",
    "estrogen",
    "progestogen",
    "camp",
    "xav939",
    "qualifying_arm",
    "n_independent_donors_in_arm",
    "donor_identity_source",
    "population",
    "assay",
    "chemistry",
    "raw_fastq_open",
    "controlled_access",
    "fcs_linked",
    "donor_overlap_documented_disjoint",
    "integrates_other_candidates",
    "notes",
    "sources",
    "retrieved_on",
)

SYSTEMS = (
    "organoid",
    "assembloid",
    "primary_culture",
    "chip",
    "tissue",
    "menstrual_effluent",
    "other",
)
IN_VITRO = frozenset({"organoid", "assembloid", "primary_culture", "chip"})
TRISTATE = ("yes", "no", "unknown")
ASSAYS = ("scRNA-seq", "snRNA-seq", "bulk RNA-seq")
#: `chemistry` is one or more of these, joined by ';'. Free text would let
#: "Smart-seq2 (not 10x)" pass a substring test for 10x.
CHEMISTRIES = (
    "10x_3p_v1",
    "10x_3p_v2",
    "10x_3p_v3",
    "10x_3p_v3.1",
    "10x_5p",
    "10x_unspecified",
    "fluidigm_c1",
    "drop_seq",
    "smart_seq2",
    "not_single_cell",
    "unknown",
)

#: A column name containing any of these tokens could carry an expression or
#: outcome quantity, so the inventory refuses it whatever it is called.
FORBIDDEN_COLUMN_TOKENS = (
    "klf12",
    "expr",
    "detect",
    "fraction",
    "quantile",
    "threshold",
    "mean",
    "median",
    "score",
    "rank",
    "adhesion",
    "outcome",
    "pregnan",
    "implant",
    "fertil",
    "umi",
)

TIER_EXACT = "T1_exact"
TIER_ONE_MISSING = "T2_one_component_missing"
TIER_CONTEXT = "T3_context_only"
TIER_NONE = "none"
TIER_UNRESOLVED = "unresolved_cocktail_metadata"

QUALIFIED = "QUALIFIED_METADATA"
BLOCKED_DONOR_OVERLAP = "BLOCKED_DONOR_OVERLAP"


class InventoryError(ValueError):
    """The inventory breaks its metadata-only contract."""


def read_inventory(text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    columns = tuple(reader.fieldnames or ())
    bad = [c for c in columns if any(t in c.lower() for t in FORBIDDEN_COLUMN_TOKENS)]
    if bad:
        raise InventoryError(
            f"columns that could carry an expression or outcome value: {bad}"
        )
    if columns != INVENTORY_COLUMNS:
        raise InventoryError(f"inventory columns must be exactly {INVENTORY_COLUMNS}")
    return list(reader)


def validate_inventory(rows: list[dict[str, str]]) -> None:
    seen: set[str] = set()
    for row in rows:
        cid = row["candidate_id"]
        if not re.fullmatch(r"C[0-9]{2}", cid) or cid in seen:
            raise InventoryError(f"candidate_id {cid!r} is malformed or repeated")
        seen.add(cid)
        for column, value in row.items():
            text = ascii_form(value or "")
            if text is None:
                raise InventoryError(f"{cid}.{column} is not ASCII after NFKC")
            if "klf12" in re.sub(r"[^a-z0-9]", "", text.casefold()):
                raise InventoryError(
                    f"{cid}.{column} mentions KLF12; the inventory is value-blind"
                )
            if names_adoc_donor(text) or names_adoc_accession(text):
                raise InventoryError(f"{cid}.{column} names an ADOC donor or accession")
        if row["system"] not in SYSTEMS:
            raise InventoryError(f"{cid}: system {row['system']!r} not in {SYSTEMS}")
        if row["assay"] not in ASSAYS:
            raise InventoryError(f"{cid}: assay {row['assay']!r} not in {ASSAYS}")
        if not set(row["chemistry"].split(";")) <= set(CHEMISTRIES):
            raise InventoryError(
                f"{cid}: chemistry {row['chemistry']!r} not in {CHEMISTRIES}"
            )
        for column in (
            "estrogen",
            "progestogen",
            "camp",
            "xav939",
            "raw_fastq_open",
            "controlled_access",
            "fcs_linked",
            "donor_overlap_documented_disjoint",
            "integrates_other_candidates",
        ):
            if row[column] not in TRISTATE:
                raise InventoryError(
                    f"{cid}.{column}={row[column]!r} not in {TRISTATE}"
                )
        n = row["n_independent_donors_in_arm"]
        if not (n == "unknown" or re.fullmatch(r"[0-9]+", n)):
            raise InventoryError(
                f"{cid}: donor count {n!r} is neither an integer nor unknown"
            )
        if not row["notes"].strip() or not row["sources"].strip():
            raise InventoryError(f"{cid}: every row needs its reasons and sources")
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", row["retrieved_on"]):
            raise InventoryError(f"{cid}: retrieved_on must be an ISO date")


def protocol_tier(row: dict[str, str]) -> str:
    """D1: in-vitro hormone-treated epithelium, tiered by cocktail completeness."""
    if row["system"] not in IN_VITRO:
        return TIER_NONE
    if row["estrogen"] != "yes" or row["progestogen"] != "yes":
        return TIER_NONE
    extras = (row["camp"], row["xav939"])
    if "unknown" in extras:
        # T2 needs the missing component RECORDED as missing; unresolved
        # treatment metadata is not a biological match at any tier.
        return TIER_UNRESOLVED
    if extras == ("yes", "yes"):
        return TIER_EXACT
    if "yes" in extras:
        return TIER_ONE_MISSING
    return TIER_CONTEXT


def qualify(row: dict[str, str], *, min_reference_donors: int) -> tuple[str, list[str]]:
    """The metadata verdict for one candidate and every reason it fails."""
    reasons: list[str] = []
    tier = protocol_tier(row)
    if tier == TIER_UNRESOLVED:
        reasons.append(
            "D1: cAMP or XAV939 status is unknown, so no tier can be assigned"
        )
    elif tier == TIER_NONE:
        reasons.append("D1: not in-vitro E2 + progestogen treated epithelium")
    elif tier == TIER_CONTEXT:
        reasons.append("D1: E2 + progestogen alone is context only")
    n = row["n_independent_donors_in_arm"]
    if n == "unknown":
        reasons.append(
            "D2: independent donors in the qualifying arm are not documented"
        )
    elif int(n) < min_reference_donors:
        reasons.append(
            f"D2: {n} independent donors < min_reference_donors={min_reference_donors}"
        )
    if row["assay"] not in ("scRNA-seq", "snRNA-seq"):
        reasons.append("RR04: not a single-cell or single-nucleus RNA assay")
    if row["raw_fastq_open"] != "yes":
        reasons.append(
            "D5: no open raw FASTQ, so the same-pipeline route is impossible"
        )
    elif not all(c.startswith("10x_") for c in row["chemistry"].split(";")):
        reasons.append(
            "D5: not 10x Chromium chemistry, so the pinned Cell Ranger stack cannot process it"
        )
    if row["controlled_access"] != "no":
        reasons.append("D8: controlled-access data are excluded from this increment")
    if row["integrates_other_candidates"] != "no":
        reasons.append("an integrated atlas double-counts its source datasets")
    if row["fcs_linked"] != "no" and row["donor_overlap_documented_disjoint"] != "yes":
        return BLOCKED_DONOR_OVERLAP, reasons + [
            "D8: FCS-linked and donor-code disjointness from SZ09/SZ10/SZ25 not documented"
        ]
    return (QUALIFIED if not reasons else "EXCLUDED"), reasons


def _chemistry_rank(chemistry: str) -> int:
    """D7 platform proximity to ADOC (10x 3' v3.1): the worst listed chemistry counts."""
    rank = {"10x_3p_v3.1": 0, "10x_3p_v3": 1}
    return max(
        rank.get(c, 2 if c.startswith("10x_") else 3) for c in chemistry.split(";")
    )


def selection_key(row: dict[str, str]) -> tuple:
    """D7: tier, then same-pipeline feasibility, donors, platform, accession."""
    tier_rank = {TIER_EXACT: 0, TIER_ONE_MISSING: 1}.get(protocol_tier(row), 9)
    return (
        tier_rank,
        0 if row["raw_fastq_open"] == "yes" else 1,
        -int(row["n_independent_donors_in_arm"]),
        _chemistry_rank(row["chemistry"]),
        row["accessions"],
    )


def select(
    rows: list[dict[str, str]], *, min_reference_donors: int
) -> list[dict[str, str]]:
    """Every metadata-qualified candidate in the frozen D7 order."""
    validate_inventory(rows)
    qualified = [
        r
        for r in rows
        if qualify(r, min_reference_donors=min_reference_donors)[0] == QUALIFIED
    ]
    return sorted(qualified, key=selection_key)


def qualification_rows(
    rows: list[dict[str, str]], *, min_reference_donors: int
) -> list[dict[str, str]]:
    order = {
        r["candidate_id"]: i + 1
        for i, r in enumerate(select(rows, min_reference_donors=min_reference_donors))
    }
    out = []
    for row in rows:
        verdict, reasons = qualify(row, min_reference_donors=min_reference_donors)
        out.append(
            {
                "candidate_id": row["candidate_id"],
                "accessions": row["accessions"],
                "protocol_tier": protocol_tier(row),
                "metadata_verdict": verdict,
                "selection_order": str(order.get(row["candidate_id"], "")),
                "reasons": "; ".join(reasons)
                if reasons
                else "all metadata criteria met",
            }
        )
    return out
