"""Post-closure corrections to the scRNA observation map, and the evidence behind them.

WHY THIS EXISTS. `config/scrna_observation_map.tsv` is frozen twice over: Phase 2B's
closure audit freezes everything under `config/` and `docs/scrna/`
(`dt_adoc.closure_replay`), and the node-support pre-registration fixes the map's
feature lists as the only genes that audit reads. A gene-identity error found after
both freezes therefore cannot be repaired in place. It is repaired here instead, as
a declared correction layer that LIVE consumers apply and that frozen and closed
analyses never see.

THE ONE CORRECTION SO FAR (OC-001, OC-002). `E_PC6` is PC6, which is PCSK5
(HGNC:8747). The frozen map measured it through PCSK6 (HGNC:8569), which is PACE4,
a different convertase. The model's own node dictionary and
`config/node_entity_map.tsv` already said PCSK5.

WHAT IT PRODUCES, all outside the frozen paths:

- `docs/scrna_corrections/scrna_observation_map_corrected.tsv`: the frozen map with
  the corrections applied, byte-identical to it everywhere else;
- `docs/scrna_corrections/pc6_pcsk5/evidence.tsv` and `findings.json`: per-unit
  PCSK5 aggregates from a POST-HOC extraction of the deposited object, computed with
  the frozen node-support statistics unchanged.

THE SAME STATISTICS, PROVEN, NOT ASSERTED. The extraction also re-reads PCSK6 and
refuses to write anything unless the re-derived PCSK6 rows reproduce the frozen
`docs/scrna/node_support_evidence.tsv` rows byte for byte. The bootstrap resamples
cells by unit ordinal and is independent of which gene columns are present, so that
check covers the PCSK5 rows too.

HISTORY STAYS READABLE AND STOPS COUNTING. `live_evidence_rows` is the frozen
evidence with every superseded row removed (`gene:PCSK6`, and `node:E_PC6`, which was
PCSK6) and the corrected rows added. Frozen artifacts are never rewritten.

TWO WAYS TO RUN THE EXTRACTION, as in `node_support`:

    extract --rds <object> --rscript <R>   extract, then derive
    derive --from-per-cell <table>         re-derive the committed numbers, no R

and `map` regenerates the corrected map. The per-cell table carries sample-level
metadata and is written OUTSIDE the repository; only per-unit aggregates are
committed.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

from dt_adoc.scrna import node_support as N
from dt_adoc.scrna import node_support_contract as C

REPO = Path(__file__).resolve().parents[3]
FROZEN_MAP = Path("config/scrna_observation_map.tsv")
CORRECTIONS = Path("config/scrna_observation_map_corrections.tsv")
CORRECTED_MAP = Path("docs/scrna_corrections/scrna_observation_map_corrected.tsv")
FROZEN_EVIDENCE = Path("docs/scrna/node_support_evidence.tsv")
PC6_DIR = Path("docs/scrna_corrections/pc6_pcsk5")
PC6_EVIDENCE = PC6_DIR / "evidence.tsv"
PC6_FINDINGS = PC6_DIR / "findings.json"
DEFAULT_PER_CELL = Path.home() / "ext/dt_adoc_node_support/pc6_pcsk5_per_cell.tsv"

CORRECTION_FIELDS = (
    "correction_id",
    "mapping_id",
    "model_node",
    "field",
    "frozen_value",
    "corrected_value",
    "status",
    "basis",
    "evidence",
)
POST_HOC = "post_hoc_correction"

#: The correction this extraction serves: the node, the gene it now reads, and the
#: gene re-read only to prove the statistics are the frozen audit's.
PC6_NODE = "E_PC6"
CORRECTED_GENE = "PCSK5"
REPRODUCED_GENE = "PCSK6"

#: HGNC records, retrieved 2026-10-13 from rest.genenames.org. Stated here so a
#: reader does not have to trust a symbol: the extraction checks the object's own
#: feature names against these symbols and records any other PCSK feature it sees.
GENE_IDENTITY = {
    "PCSK5": {
        "hgnc_id": "HGNC:8747",
        "name": "proprotein convertase subtilisin/kexin type 5",
        "alias_symbols": ["PC5", "PC6", "SPC6"],
        "ensembl_gene_id": "ENSG00000099139",
        "entrez_id": "5125",
    },
    "PCSK6": {
        "hgnc_id": "HGNC:8569",
        "name": "proprotein convertase subtilisin/kexin type 6",
        "alias_symbols": ["SPC4"],
        "previous_symbols": ["PACE4"],
        "ensembl_gene_id": "ENSG00000140479",
        "entrez_id": "5046",
    },
}

#: Appended to the frozen extraction script, which runs verbatim. It reports every
#: PCSK-family feature the object carries, case-insensitively, and any feature-level
#: metadata it holds for the two genes, so identity rests on the object as well as
#: on the symbol.
_R_IDENTITY_PROBE = """
pcsk <- sort(grep("^pcsk", rownames(cm), value = TRUE, ignore.case = TRUE))
cat(sprintf("pcsk_features\\t%s\\n", paste(pcsk, collapse = ",")), file = stderr())
mf <- tryCatch(obj[["RNA"]][[]], error = function(e) NULL)
if (is.null(mf) || ncol(mf) == 0) {
  cat("feature_metadata\\tnone\\n", file = stderr())
} else {
  for (g in c("PCSK5", "PCSK6")) {
    if (g %in% rownames(mf)) {
      vals <- vapply(mf[g, , drop = FALSE], as.character, character(1))
      cat(sprintf("feature_metadata_%s\\t%s\\n", g,
                  paste(names(vals), vals, sep = "=", collapse = ";")),
          file = stderr())
    }
  }
}
"""


class CorrectionError(RuntimeError):
    """A correction does not apply cleanly, or its evidence cannot be trusted."""


# --------------------------------------------------------------------------
# The correction layer over the frozen map
# --------------------------------------------------------------------------


def load_corrections(root: Path = REPO) -> list[dict[str, str]]:
    with (root / CORRECTIONS).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != CORRECTION_FIELDS:
            raise CorrectionError(f"{CORRECTIONS} header is not {CORRECTION_FIELDS}")
        rows = list(reader)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row["mapping_id"], row["field"])
        if key in seen:
            raise CorrectionError(f"two corrections address {key}")
        seen.add(key)
        if row["status"] != POST_HOC:
            raise CorrectionError(f"{row['correction_id']}: status must be {POST_HOC}")
    return rows


def _frozen_map(root: Path) -> tuple[list[str], list[dict[str, str]]]:
    with (root / FROZEN_MAP).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or ()), list(reader)


def corrected_map_rows(root: Path = REPO) -> tuple[list[str], list[dict[str, str]]]:
    """The frozen map with every correction applied exactly once.

    A correction whose `frozen_value` is not what the frozen map carries refuses to
    apply: the map is frozen, so a mismatch means the correction was written
    against something else.
    """
    fields, rows = _frozen_map(root)
    by_id = {row["mapping_id"]: row for row in rows}
    for fix in load_corrections(root):
        row = by_id.get(fix["mapping_id"])
        if row is None or row["model_node"] != fix["model_node"]:
            raise CorrectionError(f"{fix['correction_id']}: no matching map row")
        if fix["field"] not in fields:
            raise CorrectionError(
                f"{fix['correction_id']}: unknown field {fix['field']}"
            )
        if row[fix["field"]] != fix["frozen_value"]:
            raise CorrectionError(
                f"{fix['correction_id']}: the frozen map's {fix['field']} is "
                f"{row[fix['field']]!r}, not {fix['frozen_value']!r}"
            )
        row[fix["field"]] = fix["corrected_value"]
    return fields, rows


def render_map(fields: list[str], rows: list[dict[str, str]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fields, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def write_corrected_map(root: Path = REPO) -> Path:
    target = root / CORRECTED_MAP
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        render_map(*corrected_map_rows(root)), encoding="utf-8", newline=""
    )
    return target


def corrected_map_path(root: Path = REPO) -> Path:
    """The committed corrected map, refused if it no longer matches its inputs."""
    path = root / CORRECTED_MAP
    if path.read_text(encoding="utf-8") != render_map(*corrected_map_rows(root)):
        raise CorrectionError(
            f"{CORRECTED_MAP} is stale; regenerate it with "
            "`python -m dt_adoc.scrna.observation_corrections map`"
        )
    return path


def superseded(root: Path = REPO) -> dict[str, dict[str, tuple[str, ...]]]:
    """Per corrected node: the genes it no longer reads and the genes it now reads."""
    frozen = C.assessable_nodes(root / FROZEN_MAP)
    corrected = C.assessable_nodes(root / CORRECTED_MAP)
    changes: dict[str, dict[str, tuple[str, ...]]] = {}
    for node, row in corrected.items():
        before, after = C.features(frozen[node]), C.features(row)
        if before != after:
            changes[node] = {
                "removed": tuple(g for g in before if g not in after),
                "added": tuple(g for g in after if g not in before),
            }
    return changes


# --------------------------------------------------------------------------
# The post-hoc extraction
# --------------------------------------------------------------------------


def extract(rds: Path, destination: Path, *, rscript: str) -> dict[str, str]:
    """Run the frozen extraction script verbatim, plus the identity probe."""
    genes = ",".join(sorted({CORRECTED_GENE, REPRODUCED_GENE, *N.CONTEXT_GENES}))
    with tempfile.NamedTemporaryFile(
        "w", suffix=".R", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(N._R_EXTRACT + _R_IDENTITY_PROBE)
        script = handle.name
    try:
        completed = subprocess.run(
            [rscript, script, str(rds), str(destination), genes],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        Path(script).unlink(missing_ok=True)
    if completed.returncode != 0:
        raise CorrectionError(f"R extraction failed: {completed.stderr.strip()[:800]}")
    record: dict[str, str] = {}
    for line in completed.stderr.splitlines():
        key, _, value = line.partition("\t")
        if key in {
            "r_version",
            "seuratobject_version",
            "absent_features",
            "n_features_total",
            "pcsk_features",
            "feature_metadata",
        } or key.startswith("feature_metadata_"):
            record[key] = value.strip()
    record["rds_sha256"] = N._sha256(rds)
    record["per_cell_sha256"] = N._sha256(destination)
    N._sidecar(destination).write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return record


def _evidence_row(unit_id: str, stats: N.UnitStats, key: str, level: str, name: str):
    """One evidence row, formatted exactly as `node_support.write_artifacts` does."""
    return {
        "unit_id": unit_id,
        "donor": stats.unit.donor,
        "condition": stats.unit.condition,
        "compartment": stats.unit.compartment,
        "level": level,
        "name": name,
        "n_cells": stats.n_cells,
        "exposure": f"{stats.exposure:.6g}",
        "f": f"{stats.f[key]:.6e}",
        "f_ci_lo": f"{stats.f_ci[key][0]:.6e}",
        "f_ci_hi": f"{stats.f_ci[key][1]:.6e}",
        "d": f"{stats.d[key]:.6f}",
        "d_ci_lo": f"{stats.d_ci[key][0]:.6f}",
        "d_ci_hi": f"{stats.d_ci[key][1]:.6f}",
        "min_nonzero_value": f"{stats.min_nonzero[key]:.6e}",
    }


def _stringify(row: dict[str, object]) -> dict[str, str]:
    return {key: str(value) for key, value in row.items()}


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def derive(per_cell: Path, record: dict[str, str], *, root: Path = REPO):
    """Per-unit PCSK5 evidence, after proving the statistics reproduce PCSK6."""
    if CORRECTED_GENE in record.get("absent_features", "").split(","):
        raise CorrectionError(f"{CORRECTED_GENE} is not a feature of the object")
    binding = N.verify_source_binding(per_cell, record, root=root)
    absent = tuple(f for f in record.get("absent_features", "").split(",") if f)
    cells = N.read_per_cell(per_cell, absent)
    ordered = sorted(cells.by_unit)
    stats = {
        unit_id: N.unit_statistics(cells, unit_id, ordinal)
        for ordinal, unit_id in enumerate(ordered)
    }

    frozen = {
        (r["unit_id"], r["level"], r["name"]): r
        for r in _read_tsv(root / FROZEN_EVIDENCE)
    }
    mismatched = []
    for unit_id, row in stats.items():
        rederived = _stringify(
            _evidence_row(
                unit_id, row, f"gene:{REPRODUCED_GENE}", "gene", REPRODUCED_GENE
            )
        )
        if frozen.get((unit_id, "gene", REPRODUCED_GENE)) != rederived:
            mismatched.append(unit_id)
    frozen_units = {k[0] for k in frozen}
    if mismatched or frozen_units != set(stats):
        raise CorrectionError(
            "the re-derived PCSK6 rows do not reproduce the frozen audit "
            f"(mismatched units {mismatched}; units {sorted(frozen_units ^ set(stats))} "
            "differ), so these statistics are not the audit's and nothing is written"
        )

    evidence = []
    for unit_id, row in sorted(stats.items()):
        key = f"gene:{CORRECTED_GENE}"
        evidence.append(_evidence_row(unit_id, row, key, "gene", CORRECTED_GENE))
        # E_PC6 now has one feature, so its node aggregate IS that gene's column:
        # values @ membership with a single 1 is the column, scored on the same
        # resample. The frozen node:E_PC6 was PCSK6 and is superseded.
        evidence.append(_evidence_row(unit_id, row, key, "node", PC6_NODE))

    # The object's feature metadata is Seurat variable-feature statistics per
    # sample; what matters for identity is whether any column names a gene
    # identifier. The full probe output stays in the extraction sidecar.
    metadata = {k: v for k, v in record.items() if k.startswith("feature_metadata")}
    columns = sorted(
        {
            pair.partition("=")[0]
            for value in metadata.values()
            for pair in value.split(";")
            if "=" in pair
        }
    )
    identifier_columns = [
        c
        for c in columns
        if any(t in c.lower() for t in ("ensembl", "gene_id", "ensg"))
    ]
    epithelium = {
        unit_id: {
            gene: {"f": row.f[f"gene:{gene}"], "d": row.d[f"gene:{gene}"]}
            for gene in (CORRECTED_GENE, REPRODUCED_GENE)
        }
        for unit_id, row in sorted(stats.items())
        if row.unit.compartment == "epithelium"
    }
    findings = {
        "schema_version": 1,
        "registration_status": "post_hoc_not_preregistered",
        "corrections": [c["correction_id"] for c in load_corrections(root)],
        "node": PC6_NODE,
        "corrected_gene": CORRECTED_GENE,
        "superseded_gene": REPRODUCED_GENE,
        "gene_identity": GENE_IDENTITY,
        "object_identity_check": {
            "pcsk_features_in_object": record.get("pcsk_features", "").split(","),
            "corrected_gene_present": CORRECTED_GENE not in absent,
            "feature_metadata_columns": len(columns),
            "feature_metadata_identifier_columns": identifier_columns,
            "identity_basis": (
                "feature symbol only: the object carries no gene-identifier column, "
                "so identity rests on the HGNC symbol records in gene_identity"
                if not identifier_columns
                else "feature symbol and the identifier columns listed"
            ),
        },
        "reproduction_check": {
            "gene": REPRODUCED_GENE,
            "units_compared": len(stats),
            "rows_identical_to": str(FROZEN_EVIDENCE),
            "result": "identical",
        },
        "superseded_for_live_consumers": {
            "rows": [f"gene:{REPRODUCED_GENE}", f"node:{PC6_NODE}"],
            "frozen_artifacts_kept_unchanged": [
                str(FROZEN_MAP),
                str(FROZEN_EVIDENCE),
                "docs/scrna/node_support_findings.json",
                "docs/scrna/node_rna_interpretability.tsv",
                "docs/scrna/node_support_preregistration.md",
                "docs/phase2a/node_personalization_map.tsv",
            ],
        },
        "epithelium_detection": epithelium,
        "layer": "deposited counts layer (decontX-corrected, non-integer)",
        "layer_caveat": (
            "As in the frozen audit, every absence call on this layer is provisional: "
            "detection invariance against raw UMIs was established for KLF12 only."
        ),
        "provenance": {
            "asset_id": N.ASSET_ID,
            **binding,
            **{
                k: v
                for k, v in record.items()
                if k in {"r_version", "seuratobject_version", "n_features_total"}
            },
            "extraction_script": "node_support._R_EXTRACT verbatim, plus _R_IDENTITY_PROBE",
            "statistics": "node_support.unit_statistics, unchanged",
            "bootstrap_b": C.BOOTSTRAP_B,
            "bootstrap_seed": C.BOOTSTRAP_SEED,
            "python": sys.version.split()[0],
            "numpy": np.__version__,
        },
    }
    return evidence, findings


def write_pc6(evidence, findings, *, root: Path = REPO) -> list[Path]:
    out = root / PC6_DIR
    out.mkdir(parents=True, exist_ok=True)
    with (out / PC6_EVIDENCE.name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, list(evidence[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(evidence)
    (out / PC6_FINDINGS.name).write_text(
        json.dumps(findings, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    return [out / PC6_EVIDENCE.name, out / PC6_FINDINGS.name]


# --------------------------------------------------------------------------
# What live consumers read
# --------------------------------------------------------------------------


def live_evidence_rows(root: Path = REPO) -> list[dict[str, str]]:
    """The frozen evidence with superseded rows removed and corrected rows added."""
    changes = superseded(root)
    corrected = C.assessable_nodes(corrected_map_path(root))
    still_read = {g for row in corrected.values() for g in C.features(row)}
    removed_genes = {g for c in changes.values() for g in c["removed"]}
    if removed_genes & still_read:
        raise CorrectionError(
            f"{sorted(removed_genes & still_read)} is superseded for one node but "
            "still measured by another; dropping its rows would remove live evidence"
        )
    kept = [
        row
        for row in _read_tsv(root / FROZEN_EVIDENCE)
        if not (row["level"] == "gene" and row["name"] in removed_genes)
        and not (row["level"] == "node" and row["name"] in changes)
    ]
    added = _read_tsv(root / PC6_EVIDENCE)
    supplied = {(r["level"], r["name"]) for r in added}
    for node, change in changes.items():
        needed = {("node", node), *(("gene", g) for g in change["added"])}
        if not needed <= supplied:
            raise CorrectionError(
                f"{node}: corrected evidence lacks {needed - supplied}"
            )
    return kept + added


def absent_features(root: Path = REPO) -> frozenset[str]:
    """Absent symbols over the frozen audit and the correction extraction."""
    frozen = json.loads(
        (root / "docs/scrna/node_support_findings.json").read_text(encoding="utf-8")
    )["absent_features"]
    findings = json.loads((root / PC6_FINDINGS).read_text(encoding="utf-8"))
    extra = (
        []
        if findings["object_identity_check"]["corrected_gene_present"]
        else [CORRECTED_GENE]
    )
    return frozenset([*frozen, *extra])


def program_verdict(
    node: str,
    compartment: str,
    stats: dict[str, N.UnitStats],
    program: tuple[str, ...],
    committed: tuple[str, ...],
    expected: str,
) -> dict[str, object]:
    """`node_support.member_verdict` over an explicit program.

    The frozen function reads the frozen map through bound defaults, so it cannot
    be pointed at a corrected program. This is its decision logic over a program
    the caller supplies, and nothing else: `tests/unit/test_observation_corrections.py`
    requires it to return the frozen function's per-donor calls and verdict for
    every node on the frozen evidence.
    """
    measured = next(iter(stats.values())).f
    available = tuple(g for g in program if f"gene:{g}" in measured)
    if len(committed) >= C.MIN_VOTING_GENES and len(program) < C.MIN_VOTING_GENES:
        return {
            "verdict": "uninformative",
            "reason": "program_reduced_below_two_by_r1_r2",
            "program": list(program),
        }
    if not available:
        return {
            "verdict": "uninformative",
            "reason": "all_features_absent_from_object",
            "program": [],
        }
    if len(program) >= C.MIN_VOTING_GENES and len(available) < C.MIN_VOTING_GENES:
        return {
            "verdict": "uninformative",
            "reason": "features_absent_from_object",
            "program": list(available),
        }
    per_donor: dict[str, str] = {}
    for donor in C.DONORS:
        moves = {g: N.gene_movement(g, donor, compartment, stats) for g in available}
        if any(v == "uninformative" for v in moves.values()):
            per_donor[donor] = "uninformative"
            continue
        up = sum(v == "moves_up" for v in moves.values())
        down = sum(v == "moves_down" for v in moves.values())
        if len(available) == 1:
            called = next(iter(moves.values()))
            called = called if called in {"moves_up", "moves_down"} else None
        elif len(available) == C.MIN_VOTING_GENES:
            called = "moves_up" if up == 2 else "moves_down" if down == 2 else None
        else:
            called = (
                "moves_up"
                if up * 2 > len(available)
                else "moves_down"
                if down * 2 > len(available)
                else None
            )
        per_donor[donor] = called or "no_material_move"
    wanted = "moves_up" if expected == "OFF -> ON" else "moves_down"
    against = "moves_down" if wanted == "moves_up" else "moves_up"
    calls = list(per_donor.values())
    if any(call == "uninformative" for call in calls):
        verdict = "uninformative"
    elif all(call == wanted for call in calls):
        verdict = "concordant_with_alias"
    elif all(call == "no_material_move" for call in calls) or all(
        call == against for call in calls
    ):
        verdict = "divergent"
    else:
        verdict = "inconsistent"
    return {
        "verdict": verdict,
        "expected_cnt_to_ht": expected,
        "per_donor": per_donor,
        "program": list(available),
    }


def live_member_verdict(
    node: str, compartment: str, stats: dict[str, N.UnitStats], *, root: Path = REPO
) -> dict[str, object]:
    """The frozen verdict for an uncorrected node; the corrected program otherwise."""
    if node not in superseded(root):
        return N.member_verdict(node, compartment, stats, {})
    from dt_adoc.scrna import node_support_expectations as X

    path = corrected_map_path(root)
    expected = next(
        r["expected_cnt_to_ht"]
        for r in X.expectation_table()
        if r["model_node"] == node
    )
    return program_verdict(
        node,
        compartment,
        stats,
        C.direction_vote_programs(path)[node],
        C.features(C.assessable_nodes(path)[node]),
        expected,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m dt_adoc.scrna.observation_corrections"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("map", help="regenerate the corrected observation map")
    ext = sub.add_parser("extract", help="extract PCSK5 from the object, then derive")
    ext.add_argument("--rds", type=Path, required=True)
    ext.add_argument("--rscript", default="Rscript")
    ext.add_argument("--per-cell-out", type=Path, default=DEFAULT_PER_CELL)
    der = sub.add_parser("derive", help="re-derive from an extracted per-cell table")
    der.add_argument("--from-per-cell", type=Path, required=True)
    for p in (ext, der):
        p.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    if args.command == "map":
        print(f"wrote {write_corrected_map(REPO).relative_to(REPO)}")
        return 0
    if args.command == "extract":
        args.per_cell_out.parent.mkdir(parents=True, exist_ok=True)
        record = extract(args.rds, args.per_cell_out, rscript=args.rscript)
        per_cell = args.per_cell_out
    else:
        per_cell = args.from_per_cell
        record = N.extraction_provenance(per_cell)
    evidence, findings = derive(per_cell, record, root=REPO)
    if args.no_write:
        print(json.dumps(findings, indent=1, sort_keys=True))
        return 0
    for path in write_pc6(evidence, findings, root=REPO):
        print(f"wrote {path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
