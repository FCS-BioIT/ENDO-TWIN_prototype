#!/usr/bin/env python3
"""Validate the proposed U1 mutation contract.

The contract (docs/v05_u1_mutation_contract_2026-10-22.tsv) is a PROPOSAL. U1 has
not been authorized and no canonical ledger has been modified. This script checks
that the proposal is well formed and executable, at TWO explicitly separated
levels.

  REPOSITORY LEVEL (default)
      Runs from a clean checkout containing only tracked files. It never opens a
      PDF and never claims to have verified one. It checks contract schema and
      required fields, the exact proposed mutations and their target artifacts,
      uniqueness of row identifiers, DOI and SHA-256 syntax, consistency between
      the contract, the canonical manifests and the reconciliation table, the
      exact expected mutation counts, and the absence of unauthorized
      canonical-ledger modifications.

  LOCAL-SOURCE VERIFICATION (--verify-sources)
      Additionally hashes every PDF the contract names and compares it with the
      recorded SHA-256. It FAILS if a file is missing, if its digest differs, or
      if it cannot be associated with its declared source. The literature corpus
      is gitignored, so this level can only run in a working tree that holds it.

Successful LOCAL-SOURCE VERIFICATION is a MANDATORY PRECONDITION for executing
U1. Repository-level success alone does NOT authorize execution: it establishes
that the contract is coherent, not that the sources are the ones it names.

Exit 0 if the selected level passes, 1 otherwise. Read-only: writes nothing.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "docs" / "v05_u1_mutation_contract_2026-10-22.tsv"
PDF_MANIFEST = ROOT / "context" / "literature" / "pdf_manifest.tsv"
ACTIVE_MANIFEST = ROOT / "context" / "literature" / "active_evidence_manifest.tsv"
EVIDENCE_REGISTER = ROOT / "context" / "evidence-register.tsv"
RECONCILIATION = ROOT / "docs" / "v05_literature_corpus_reconciliation_2026-10-21.tsv"
REFERENCES = ROOT / "context" / "literature" / "references.tsv"
PDF_DIR = ROOT / "context" / "literature" / "pdfs"

CANONICAL_LEDGERS = (PDF_MANIFEST, ACTIVE_MANIFEST, EVIDENCE_REGISTER)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
MANIFEST_ID_RE = re.compile(r"^PDF-\d{3}$")

CONTRACT_FIELDS = [
    "contract_id", "source_doi", "source_sha256", "canonical_artifact",
    "operation", "row_identifier", "fields_changed", "expected_old_state",
    "expected_new_state", "supporting_primary_evidence", "validation",
]

EXPECTED_APPENDS = 31
EXPECTED_UPDATES = 0  # PDF-048 is NO_CHANGE: see contract U1-P-01
EXPECTED_NO_CHANGE = 4
EXPECTED_UPDATE_DERIVED = 1
EXPECTED_BLOCKED = 0  # Paule 2015 DOI resolved 2026-10-22; nothing blocked
EXPECTED_ACTIVE_ROWS = 50
EXPECTED_EVIDENCE_ROWS = 47
EXPECTED_U1_TOTAL_APPENDS = 31  # 30 specified + 1 blocked on an unresolved DOI
EXPECTED_PRE_DELTA_SCOPE = 24
EXPECTED_EXCLUDED = 2  # Fitzgerald 2023 and Zhou 2026, owner-excluded backlog

# PDF-048 is re-registered against the locally held rendering. Changing the
# rendering changes more than the digest, so the fields are named here and the
# contract is asserted to declare all of them.
PDF048_REQUIRED_FIELDS = {"sha256", "pages", "rendering_read"}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def git_clean(paths: tuple[Path, ...]) -> tuple[bool | None, str]:
    """Ledger immutability relative to HEAD.

    Returns (state, detail) where state is True (established clean), False
    (a ledger is modified) or **None (NOT ESTABLISHED)**. None is returned
    outside a git work tree, and the caller must not count it as established:
    a clean checkout cannot demonstrate immutability, only decline to claim it.
    """
    rel = [str(p.relative_to(ROOT)) for p in paths]
    try:
        proc = subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain", "--", *rel],
            capture_output=True, text=True, timeout=60, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover
        return None, f"NOT ESTABLISHED - git unavailable ({exc.__class__.__name__})"
    if proc.returncode != 0:
        return None, "NOT ESTABLISHED - not a git work tree, immutability unchecked"
    dirty = [line for line in proc.stdout.splitlines() if line.strip()]
    if dirty:
        return False, "; ".join(dirty)
    return True, "ESTABLISHED - clean relative to HEAD"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the proposed U1 mutation contract.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--verify-sources", action="store_true",
        help="additionally hash every PDF the contract names and require an "
             "exact match; needs the gitignored literature corpus",
    )
    args = parser.parse_args()

    failures: list[str] = []
    notes: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    # ---------------- repository level ----------------------------------
    for path in (CONTRACT, PDF_MANIFEST, ACTIVE_MANIFEST, EVIDENCE_REGISTER,
                 RECONCILIATION, REFERENCES):
        if not path.is_file():
            print(f"check_u1_mutation_contract: FAILED - tracked input missing: "
                  f"{path.relative_to(ROOT)}")
            return 1

    contract = read_tsv(CONTRACT)
    manifest = read_tsv(PDF_MANIFEST)
    active = read_tsv(ACTIVE_MANIFEST)
    evidence = read_tsv(EVIDENCE_REGISTER)
    reconciliation = read_tsv(RECONCILIATION)

    # schema
    check(
        list(contract[0].keys()) == CONTRACT_FIELDS,
        f"contract header is {list(contract[0].keys())}, expected {CONTRACT_FIELDS}",
    )
    for row in contract:
        missing = [f for f in ("contract_id", "canonical_artifact", "operation",
                               "row_identifier", "fields_changed",
                               "expected_old_state", "expected_new_state",
                               "validation") if not row.get(f, "").strip()]
        check(not missing, f"{row.get('contract_id','?')}: empty required field(s) {missing}")

    appends = [r for r in contract if r["operation"] == "APPEND_ROW"]
    updates = [r for r in contract if r["operation"] == "UPDATE_FIELDS"]
    no_change = [r for r in contract if r["operation"] == "NO_CHANGE"]
    derived = [r for r in contract if r["operation"] == "UPDATE_DERIVED"]
    blocked = [r for r in contract if r["operation"] == "BLOCKED_UNSPECIFIED"]
    excluded = [r for r in contract if r["operation"] == "EXCLUDED_BY_OWNER"]
    needs_owner = [r for r in contract if r["operation"] == "REQUIRES_OWNER_APPROVAL"]

    check(len(appends) == EXPECTED_APPENDS,
          f"expected {EXPECTED_APPENDS} APPEND_ROW rows, found {len(appends)}")
    check(len(updates) == EXPECTED_UPDATES,
          f"expected {EXPECTED_UPDATES} UPDATE_FIELDS row, found {len(updates)}")
    check(len(no_change) == EXPECTED_NO_CHANGE,
          f"expected {EXPECTED_NO_CHANGE} NO_CHANGE rows, found {len(no_change)}")
    check(len(derived) == EXPECTED_UPDATE_DERIVED,
          f"expected {EXPECTED_UPDATE_DERIVED} UPDATE_DERIVED row, found {len(derived)}")
    check(len(blocked) == EXPECTED_BLOCKED,
          f"expected {EXPECTED_BLOCKED} BLOCKED_UNSPECIFIED row(s), found {len(blocked)}")
    check(len(excluded) == EXPECTED_EXCLUDED - 1,
          f"expected 1 EXCLUDED_BY_OWNER row, found {len(excluded)}")
    check(len(appends) + len(updates) + len(no_change) + len(derived) + len(blocked)
          + len(excluded) + len(needs_owner) == len(contract),
          "contract contains an operation outside the declared kinds")
    check(len(appends) + len(blocked) == EXPECTED_U1_TOTAL_APPENDS,
          f"specified appends {len(appends)} + blocked {len(blocked)} must equal the "
          f"{EXPECTED_U1_TOTAL_APPENDS}-row append scope")

    for row in appends:
        check(row["canonical_artifact"] == "context/literature/pdf_manifest.tsv",
              f"{row['contract_id']}: APPEND_ROW must target pdf_manifest.tsv, "
              f"not {row['canonical_artifact']}")

    existing_digests = {r["sha256"] for r in manifest}
    existing_dois = {r["doi"] for r in manifest}
    existing_ids = {r["manifest_id"] for r in manifest}
    active_digests = {r["pdf_sha256"] for r in active if r["pdf_sha256"].strip()}
    recon_by_digest = {r["sha256"]: r for r in reconciliation}

    seen_digests: set[str] = set()
    seen_dois: set[str] = set()
    seen_ids: set[str] = set()

    for row in appends + updates:
        cid, digest, doi = row["contract_id"], row["source_sha256"], row["source_doi"]
        check(bool(SHA256_RE.match(digest)), f"{cid}: sha256 is not 64 lowercase hex")
        check(bool(DOI_RE.match(doi)), f"{cid}: doi is not well formed: {doi!r}")
        check(digest not in seen_digests, f"{cid}: duplicate digest within the contract")
        # A DOI may legitimately repeat: two renderings of ONE article share it
        # (Retis-Resendiz 2024 is held twice). The DIGEST is what must be unique.
        if doi in seen_dois:
            notes.append(
                f"{cid}: DOI {doi} appears on more than one row - article-versus-"
                "rendering multiplicity, permitted because the digests differ"
            )
        seen_digests.add(digest)
        seen_dois.add(doi)
        if digest.endswith("..."):
            continue
        check(digest in recon_by_digest,
              f"{cid}: digest {digest[:12]} has no row in the corpus reconciliation")

    for row in appends:
        cid, mid = row["contract_id"], row["row_identifier"]
        check(bool(MANIFEST_ID_RE.match(mid)), f"{cid}: bad manifest_id {mid!r}")
        check(mid not in existing_ids, f"{cid}: manifest_id {mid} already exists")
        check(mid not in seen_ids, f"{cid}: manifest_id {mid} proposed twice")
        seen_ids.add(mid)
        check(row["source_sha256"] not in existing_digests,
              f"{cid}: digest already registered in pdf_manifest - would duplicate")
        check(row["source_doi"] not in existing_dois,
              f"{cid}: DOI already registered in pdf_manifest - would duplicate")
        check(row["source_sha256"] not in active_digests,
              f"{cid}: digest already in active_evidence_manifest - would duplicate")
        # tests/unit/test_pdf_manifest.py forbids registered + empty ref_id.
        # Parse the DECLARED value, not any mention of the word: the row's own
        # rationale quotes the forbidden combination when explaining it.
        declared = re.search(r"registration_decision=(\w+)", row["expected_new_state"])
        check(declared is not None,
              f"{cid}: expected_new_state declares no registration_decision")
        ref_by_doi = {r["doi"].strip().lower(): r["ref_id"] for r in read_tsv(REFERENCES)}
        in_bib = ref_by_doi.get(row["source_doi"].strip().lower())
        if declared:
            if in_bib:
                check(declared.group(1) == "registered",
                      f"{cid}: DOI is in references.tsv as {in_bib}, so the row must "
                      "declare registration_decision=registered")
                check(f"ref_id={in_bib}" in row["expected_new_state"],
                      f"{cid}: must declare ref_id={in_bib}")
            else:
                check(declared.group(1) != "registered",
                      f"{cid}: declares registration_decision=registered with an empty "
                      "ref_id, which test_registration_decision_agrees_with_the_registry"
                      "_both_ways forbids")
                check("ref_id=EMPTY" in row["expected_new_state"],
                      f"{cid}: expected_new_state must state ref_id=EMPTY explicitly")

    if appends and not failures:
        nums = sorted(int(r["row_identifier"].split("-")[1]) for r in appends)
        highest = max(int(m.split("-")[1]) for m in existing_ids if MANIFEST_ID_RE.match(m))
        check(nums == list(range(highest + 1, highest + 1 + len(nums))),
              f"proposed manifest_ids {nums} are not contiguous above PDF-{highest:03d}")

    # the UPDATE row: target exists, recorded digest is not held, all changed
    # fields are declared
    for row in updates:
        cid, mid = row["contract_id"], row["row_identifier"]
        target = [r for r in manifest if r["manifest_id"] == mid]
        check(len(target) == 1, f"{cid}: {mid} does not identify exactly one row")
        if target:
            recorded = target[0]["sha256"]
            # The reconciliation carries an ABSENT_LOCALLY sentinel row for
            # registered-but-unheld renderings, so membership there does NOT
            # mean the digest resolves to a file.
            held = [
                r for r in reconciliation
                if r["sha256"] == recorded and r["relative_path"] != "ABSENT_LOCALLY"
            ]
            check(not held,
                  f"{cid}: {mid} recorded digest is held locally, nothing to repair")
            check(recorded != row["source_sha256"],
                  f"{cid}: {mid} already records the replacement rendering")
            declared = {f.strip() for f in row["fields_changed"].split("|") if f.strip()}
            missing = PDF048_REQUIRED_FIELDS - declared
            check(not missing,
                  f"{cid}: changing the rendering also changes {sorted(missing)}, "
                  "which fields_changed does not declare")

    # NO_CHANGE artifacts are in their declared state
    for row in no_change:
        cid, artifact = row["contract_id"], row["canonical_artifact"]
        if artifact.endswith("active_evidence_manifest.tsv"):
            check(len(active) == EXPECTED_ACTIVE_ROWS,
                  f"{cid}: active_evidence_manifest has {len(active)} rows, "
                  f"contract declares {EXPECTED_ACTIVE_ROWS}")
            for digest in seen_digests:
                check(digest not in active_digests,
                      f"{cid}: a contract digest is already in active_evidence_manifest")
        elif artifact.endswith("evidence-register.tsv"):
            check(len(evidence) == EXPECTED_EVIDENCE_ROWS,
                  f"{cid}: evidence-register has {len(evidence)} rows, "
                  f"contract declares {EXPECTED_EVIDENCE_ROWS}")
            lit = [r for r in evidence if r["evidence_id"].startswith("LIT-")]
            check(all(r["planned_use"] == "construction" for r in lit),
                  f"{cid}: a LIT- row no longer declares planned_use=construction")
        elif artifact.endswith("pdf_manifest.tsv"):
            target = [r for r in manifest if r["manifest_id"] == row["row_identifier"]]
            check(len(target) == 1,
                  f"{cid}: {row['row_identifier']} does not identify exactly one row")
            if target:
                expected = {"PDF-048": "author_manuscript", "PDF-034": "unrecorded"}
                want = expected.get(row["row_identifier"])
                if want:
                    check(target[0]["rendering_read"] == want,
                          f"{cid}: {row['row_identifier']} rendering_read is "
                          f"{target[0]['rendering_read']!r}, expected {want!r}; the "
                          "audit-preserving rationale needs re-checking")
        else:
            failures.append(f"{cid}: unexpected NO_CHANGE artifact {artifact!r}")

    # U1's total append scope, derived from tracked artifacts only
    excluded_row = [r for r in contract if r["operation"] == "EXCLUDED_BY_OWNER"]
    excluded_digests = {
        frag.strip().rstrip(".")
        for row in excluded_row
        for frag in row["source_sha256"].split("|")
    }
    adjudicated = [r for r in reconciliation if r["adjudicated_2026_10_21"].strip()]
    unregistered = [
        r for r in adjudicated
        if r["sha256"] not in existing_digests
        and r["sha256"] not in active_digests
        and r["relative_path"] != "ABSENT_LOCALLY"
        and not any(r["sha256"].startswith(e.rstrip(".")) for e in excluded_digests if e)
        # the replacement rendering of an already-registered article is a
        # provenance repair, not a new registration
        and not r["article_also_registered_as"].strip()
    ]
    pre_delta = [r for r in unregistered if r["sha256"] not in seen_digests]
    del pre_delta
    check(len(unregistered) == EXPECTED_U1_TOTAL_APPENDS,
          f"U1 total append scope is {len(unregistered)} adjudicated-and-unregistered "
          f"articles, contract documents {EXPECTED_U1_TOTAL_APPENDS}")
    specified_or_blocked = {r["source_sha256"] for r in appends} | {
        r["source_sha256"] for r in blocked
    }
    unspecified = [r for r in unregistered if r["sha256"] not in specified_or_blocked]
    check(not unspecified,
          f"{len(unspecified)} append-scope article(s) have no contract row: "
          + ", ".join(r["relative_path"][:48] for r in unspecified[:3]))

    # no unauthorized canonical-ledger modification
    ledgers_ok, ledger_detail = git_clean(CANONICAL_LEDGERS)
    check(ledgers_ok is not False,
          f"a canonical ledger is modified in the work tree: {ledger_detail}")

    # ---------------- local-source verification -------------------------
    source_lines: list[str] = []
    if args.verify_sources:
        # Finding 3: the prerequisite is the FULL append scope U1 will register,
        # not only the rows the contract happens to name individually. Verifying
        # the eight contract-named PDFs does NOT satisfy it.
        scope = {r["sha256"]: r for r in unregistered}
        for row in updates:
            recon = recon_by_digest.get(row["source_sha256"])
            if recon is not None:
                scope[row["source_sha256"]] = recon

        specified = (
            {r["source_sha256"] for r in appends}
            | {r["source_sha256"] for r in updates}
            | {r["source_sha256"] for r in blocked}
        )
        unspecified = [d for d in scope if d not in specified]
        if unspecified:
            failures.append(
                f"U1 is NOT execution-ready: {len(unspecified)} of {len(scope)} sources in "
                "the append scope are not individually specified in the contract "
                "(no contract row, so no DOI, target id or expected state). "
                "Source verification cannot stand in for an unwritten specification."
            )

        no_doi = sorted(
            r["relative_path"]
            for r in scope.values()
            if not (r.get("source_doi") or "").strip()
        )
        if no_doi:
            failures.append(
                f"{len(no_doi)} of {len(scope)} sources have no DOI, and "
                "pdf_manifest.tsv requires one on every row (test_every_entry_has_a_"
                "doi_and_a_content_hash). Blocked: " + "; ".join(p[:52] for p in no_doi)
            )

        verified = 0
        for digest, recon in sorted(scope.items(), key=lambda kv: kv[1]["relative_path"]):
            pdf = PDF_DIR / recon["relative_path"]
            if not pdf.is_file():
                failures.append(
                    f"source PDF missing at context/literature/pdfs/{recon['relative_path']}"
                )
                continue
            actual = hashlib.sha256(pdf.read_bytes()).hexdigest()
            if actual != digest:
                failures.append(
                    f"digest mismatch for {recon['relative_path']!r}: "
                    f"file is {actual[:12]}, reconciliation says {digest[:12]}"
                )
                continue
            verified += 1
        source_lines.append(
            f"    {verified}/{len(scope)} append-scope sources hashed and matched"
        )
    else:
        corpus_present = PDF_DIR.is_dir() and any(PDF_DIR.rglob("*.pdf"))
        notes.append(
            "local-source verification NOT performed (repository level only). "
            + ("The corpus is present here; run with --verify-sources to check it."
               if corpus_present else
               "The gitignored literature corpus is absent from this checkout, which "
               "is expected in a clean clone or a review snapshot.")
        )

    # ---------------- report --------------------------------------------
    level = "LOCAL-SOURCE VERIFICATION" if args.verify_sources else "REPOSITORY LEVEL"
    if failures:
        print(f"check_u1_mutation_contract [{level}]: FAILED ({len(failures)} problem(s))")
        for item in failures:
            print(f"  - {item}")
        if args.verify_sources:
            print("  U1 MUST NOT be executed: local-source verification is a "
                  "mandatory precondition and it did not pass.")
        return 1

    print(f"check_u1_mutation_contract [{level}]: OK")
    print(f"  {len(appends)} APPEND_ROW, all absent from both digest-bearing ledgers")
    print(f"  {len(updates)} UPDATE_FIELDS, {len(derived)} UPDATE_DERIVED, "
          f"{len(blocked)} BLOCKED_UNSPECIFIED")
    print(f"  {len(no_change)} NO_CHANGE artifacts verified to be in their declared state")
    print(f"  U1 append scope {len(unregistered)}: {len(appends)} specified, "
          f"{len(blocked)} blocked on an unresolved DOI, {len(excluded)} owner-excluded group(s)")
    print(f"  canonical ledgers: {ledger_detail}")
    if args.verify_sources:
        for line in source_lines:
            print(line)
        print("  local-source precondition for U1 execution: SATISFIED in this tree")
    for note in notes:
        print(f"  NOTE: {note}")
    if not args.verify_sources:
        print("  local-source precondition for U1 execution: NOT ESTABLISHED here")
    return 0


if __name__ == "__main__":
    sys.exit(main())
