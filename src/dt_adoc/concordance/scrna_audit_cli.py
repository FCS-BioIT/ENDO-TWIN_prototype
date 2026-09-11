"""Audit the local integrated Seurat object and record what it holds.

Deliberately a separate task rather than part of `build-concordance`: it streams
roughly 5 GB of decompressed bytes and takes minutes, and its answer changes only
when the source file does. `config/data_manifest.tsv` pins that file by hash, so
a changed object is detectable without re-running this.
"""

from __future__ import annotations

from pathlib import Path

from dt_adoc.concordance.scrna_audit import audit_object, write_audit
from dt_adoc.model.provenance import repo_root

SOURCE = Path("data") / "combined-dataset-patient-integration.rds"
DESTINATION = Path("docs") / "concordance" / "scrna_object_audit.json"


def main() -> None:
    root = repo_root()
    source = root / SOURCE
    if not source.exists():
        raise SystemExit(
            f"{SOURCE} is absent. It is a local-only, gitignored source pinned by "
            "sha256 in config/data_manifest.tsv; the audit cannot be run on a "
            "clone that lacks it, and its recorded result must not be assumed."
        )
    audit = audit_object(source)
    destination = write_audit(audit, root / DESTINATION)
    print(f"{destination}: {audit.conclusion}")


if __name__ == "__main__":
    main()
