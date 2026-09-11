"""Audit what the ADOC integrated Seurat object actually contains, without R.

Eleven rows of the concordance table are not assessable because the paper's
final single-cell annotations are not in the repository. That is a strong claim
and it was previously recorded as prose from a one-off audit
(`docs/data-inventory.md`), which a reader cannot check and a later maintainer
cannot re-run. This module turns it into a reproducible audit.

No R, no Seurat, no `readRDS`. The object is a 3.4 GB gzip-compressed R
serialization holding a 78,724 x 61,843 count matrix; loading it to read a
dozen column names would need tens of gigabytes of memory and a runtime the
repository does not declare. `AGENTS.md` forbids loading it merely to test
runtime availability, and this audit does not need it: every field name, factor
level and recorded command in an R serialization is stored as a plain
``CHARSXP`` byte string, so streaming the decompressed bytes and reading those
strings answers the question directly.

What this method does and does not establish, stated plainly because the
conclusion is an absence:

* **Presence is exact.** A name reported here was read verbatim out of the
  stream. `meta.data`'s column roster and `active.ident`'s factor levels are
  therefore facts about the file.
* **Absence is narrower than it looks, and the field names say so.** The result
  is ``annotation_tokens_absent``: no *listed* token occurs anywhere in the
  stream. It is deliberately **not** called "no annotation exists". A
  case-sensitive whitelist cannot exclude an annotation stored under a name
  nobody anticipated, a purely numeric cluster column, or a label vocabulary
  this list does not contain, and no amount of scanning turns a token search into
  a schema proof.

  What makes the conclusion usable anyway is that the tokens are the ones Seurat
  itself writes: a clustering result is stored as ``seurat_clusters`` or
  ``<assay>_snn_res.<r>``, and the call is recorded in the ``commands`` slot as
  ``FindClusters`` / ``FindNeighbors``. Finding none of them, alongside a
  ``meta.data`` roster read verbatim and an ``active.ident`` whose levels are the
  six samples rather than clusters, is strong evidence. It is evidence, not
  proof, and a structural check with R/Seurat or a full serialization parser
  would settle it; neither is available in this environment, and
  ``r_seurat_available`` records that rather than implying the check was done and
  passed.

The audit therefore bounds what the single-cell rows may claim. It cannot
supply the missing annotations, and nothing here reconstructs them: a clustering
of my own would be a comparison of the model against my reanalysis, reported
under a heading that promises the paper's populations.
"""

from __future__ import annotations

import gzip
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

#: Column names the paper's final analysis would have to carry for the
#: single-cell block to become assessable. Searched for over the whole stream.
#: Presence of any one of these is what would change the audit's conclusion.
ANNOTATION_TOKENS = (
    b"seurat_clusters",
    b"snn_res",
    b"cell_type",
    b"celltype",
    b"cellType",
    b"CellType",
    b"annotation",
    b"Annotation",
    b"predicted.id",
    b"predicted.celltype",
    b"FindClusters",
    b"FindNeighbors",
)

#: Population names the manuscript reports for its seven final populations, plus
#: the label-transfer vocabulary its Fig. 3H uses. Searched for separately from
#: the column names because an annotation could be stored under an unexpected
#: column but would still spell its own levels.
POPULATION_TOKENS = (
    b"Luminal",
    b"Glandular",
    b"Ciliated",
    b"Myofibroblast",
    b"Fibroblast",
    b"Perivascular",
    b"Endothelial",
    b"Lymphocyte",
    b"Macrophage",
    b"Decidual",
    b"Secretory",
    b"Epithelial",
    b"Stromal",
)

#: The anchor that identifies the `meta.data` column roster: `orig.ident` is the
#: first column Seurat writes and is always present.
_META_ANCHOR = b"orig.ident"

#: Field names are stored as plain ASCII runs. Four characters is short enough to
#: catch `runs` and long enough to exclude serialization padding.
_NAME_RUN = re.compile(rb"[A-Za-z][A-Za-z0-9._]{3,40}")

#: A cell barcode: donor, condition and a 10x sequence. The `meta.data` column
#: roster is immediately followed in the stream by the row names, which are these
#: barcodes, so the first one marks the end of the roster. Without this stop the
#: audit would report barcodes as if they were metadata columns.
_CELL_BARCODE = re.compile(r"SZ\d+TE_(CNT|HT)_[ACGT]+")

_CHUNK = 1 << 24


@dataclass(frozen=True)
class ScrnaObjectAudit:
    """What the integrated object holds, and what it therefore cannot support."""

    source_path: str
    source_sha256: str
    compressed_bytes: int
    decompressed_bytes: int
    #: `meta.data` column names, in file order.
    meta_data_columns: tuple[str, ...]
    #: `active.ident` factor levels. For this object these are the six
    #: donor-condition samples, which is what an unclustered object identifies
    #: cells by.
    active_ident_levels: tuple[str, ...]
    #: Annotation/clustering tokens actually found anywhere in the stream.
    annotation_tokens_found: tuple[str, ...]
    #: Manuscript population names actually found anywhere in the stream.
    population_tokens_found: tuple[str, ...]
    #: Every token searched for, so the absence claim is checkable.
    annotation_tokens_searched: tuple[str, ...]
    population_tokens_searched: tuple[str, ...]
    #: True when none of the listed tokens occurs anywhere in the stream.
    #: Narrower than "the object carries no annotation": see the module
    #: docstring. Renamed from ``final_annotations_absent``, which asserted more
    #: than a token scan can establish.
    annotation_tokens_absent: bool
    #: Whether a structural check with R/Seurat was possible here. False means
    #: the conclusion rests on the token scan alone.
    r_seurat_available: bool

    @property
    def conclusion(self) -> str:
        if not self.annotation_tokens_absent:
            return (
                "annotation-bearing tokens were found; re-audit before treating "
                "the single-cell block as unassessable."
            )
        return (
            "no listed clustering or cell-type token occurs anywhere in the "
            "stream, the meta.data roster carries none, and active.ident "
            "identifies cells by sample rather than by cluster. Consistent with "
            "a pre-annotation integrated object, on a token scan rather than a "
            "structural parse: the paper's final populations cannot be linked to "
            "these cells from this file plus this evidence."
        )


def _r_seurat_available() -> bool:
    """Whether a structural check with R/Seurat could be run here.

    `AGENTS.md` requires an unavailable R/Seurat gate to be reported rather than
    its result inferred, so the audit records the answer instead of quietly
    presenting a token scan as if it were a schema check.
    """
    import shutil

    return shutil.which("Rscript") is not None


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def _names_after(buf: bytes, anchor_end: int, limit: int = 600) -> list[str]:
    """Read the ASCII name runs that follow a `names` anchor.

    R writes a character vector as a length followed by one ``CHARSXP`` per
    element, each a length and then raw bytes, so the element names appear as
    ASCII runs separated by a few binary bytes. Reading the runs in order
    recovers the roster; the window is bounded so a long matrix region cannot be
    mistaken for field names.
    """
    window = buf[anchor_end - len(_META_ANCHOR) : anchor_end + limit]
    names: list[str] = []
    for match in _NAME_RUN.finditer(window):
        name = match.group().decode("ascii")
        if _CELL_BARCODE.fullmatch(name):
            break
        names.append(name)
    return names


def audit_object(path: Path) -> ScrnaObjectAudit:
    """Stream the object once and report its identifying fields.

    One pass. The count matrix dominates the stream, so this reads roughly 5 GB
    of decompressed bytes and takes minutes rather than seconds; it is a manual
    audit task, deliberately not part of the default test run.
    """
    meta_columns: list[str] = []
    ident_levels: list[str] = []
    found_annotation: set[bytes] = set()
    found_population: set[bytes] = set()
    decompressed = 0

    with gzip.open(path, "rb") as handle:
        tail = b""
        while True:
            chunk = handle.read(_CHUNK)
            if not chunk:
                break
            decompressed += len(chunk)
            buf = tail + chunk

            for token in ANNOTATION_TOKENS:
                if token in buf:
                    found_annotation.add(token)
            for token in POPULATION_TOKENS:
                if token in buf:
                    found_population.add(token)

            if not meta_columns:
                index = buf.find(_META_ANCHOR)
                if index >= 0:
                    meta_columns = _names_after(buf, index + len(_META_ANCHOR))

            if not ident_levels:
                index = buf.find(b"levels")
                if index >= 0:
                    candidates = _names_after(buf, index + len(b"levels"), limit=300)
                    ident_levels = [
                        name
                        for name in candidates
                        if re.fullmatch(r"SZ\d+TE_\w+", name)
                    ]

            tail = buf[-1024:]

    return ScrnaObjectAudit(
        source_path=str(path),
        source_sha256=_sha256(path),
        compressed_bytes=path.stat().st_size,
        decompressed_bytes=decompressed,
        meta_data_columns=tuple(meta_columns),
        active_ident_levels=tuple(ident_levels),
        annotation_tokens_found=tuple(
            sorted(t.decode("ascii") for t in found_annotation)
        ),
        population_tokens_found=tuple(
            sorted(t.decode("ascii") for t in found_population)
        ),
        annotation_tokens_searched=tuple(t.decode("ascii") for t in ANNOTATION_TOKENS),
        population_tokens_searched=tuple(t.decode("ascii") for t in POPULATION_TOKENS),
        annotation_tokens_absent=not found_annotation and not found_population,
        r_seurat_available=_r_seurat_available(),
    )


def write_audit(audit: ScrnaObjectAudit, destination: Path) -> Path:
    payload = {
        "schema_version": "1.0",
        "method": (
            "single streaming pass over the decompressed R serialization; field "
            "names and factor levels read as CHARSXP byte strings. No R, no "
            "Seurat, no readRDS -- see r_seurat_available. Presence is exact. "
            "Absence is LITERAL TOKEN ABSENCE over the recorded lists, not a "
            "structural proof that the object carries no annotation, and must "
            "not be cited as one."
        ),
        "conclusion": audit.conclusion,
        **asdict(audit),
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return destination
