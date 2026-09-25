"""Phase 2B: the ONLY entry point that reads a candidate reference's KLF12 values.

`open_reference_values` calls `guard.assert_rules_frozen` before it touches any
file, so no candidate value can be read until the rules pre-registration is
committed, unmodified, and its pinned implementation still hashes as frozen.

The ADOC exclusion is bound to content as well as to labels:

- the per-cell table is read ONCE, and the bytes hashed are the bytes parsed;
- a provenance sidecar (`PROVENANCE_COLUMNS`) must name a non-ADOC accession,
  the per-cell table's sha256, and every input FASTQ with two md5 values: the
  one the retrieval step computed and the one the archive publishes. This
  module computes no FASTQ md5 itself; it requires the two recorded values to
  agree, and neither may be an ADOC FASTQ's (`adoc_identity_denylist.json`),
  whatever the file is called. That the retrieval step really hashed the
  bytes it processed is the C4 provenance record's obligation;
- any source under `data/`, or hashing to the ADOC object or a `data/` file,
  is refused;
- every donor id must be a well-formed, non-ADOC id (`identity.donor_key`),
  and ids differing only in case are one donor.

The per-cell table carries no barcode: exactly `donor_id`, `klf12_count` and
`depth` (KLF12 and the column sum, both on the decontX-corrected layer), with
plain decimal numbers.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
from pathlib import Path

from dt_adoc.personalization.phase2a_contract import forbidden_reference_shas
from dt_adoc.personalization.phase2b.derivation import DonorCells
from dt_adoc.personalization.phase2b.guard import assert_rules_frozen
from dt_adoc.personalization.phase2b.identity import (
    IdentityError,
    adoc_fastq_md5s,
    ascii_form,
    donor_key,
    names_adoc_accession,
    names_adoc_donor,
)

PER_CELL_COLUMNS = ("donor_id", "klf12_count", "depth")
PROVENANCE_COLUMNS = ("source_accession", "per_cell_table_sha256", "input_files")
_NUMBER = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?")
_MD5 = re.compile(r"[0-9a-f]{32}")
#: A feature's count is part of its cell's column sum, so it can never exceed
#: it; the relative tolerance absorbs only floating-point rounding of the
#: decontX-corrected (non-integer) values.
COUNT_DEPTH_TOLERANCE = 1e-9


class ValueAccessError(RuntimeError):
    """A candidate value may not be read from this input."""


def _inside(root: Path, path: Path) -> Path:
    resolved = path.resolve()
    if resolved.is_relative_to(root / "data"):
        raise ValueAccessError(
            f"{path} is under data/: ADOC evidence is never a reference"
        )
    if not resolved.is_file():
        raise ValueAccessError(f"{path} does not exist")
    return resolved


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """json.loads keeps the LAST of a repeated key, hiding the first; refuse instead."""
    keys = [k for k, _ in pairs]
    if len(set(keys)) != len(keys):
        raise ValueAccessError(f"the provenance repeats a key: {sorted(keys)}")
    return dict(pairs)


def check_provenance(provenance: dict, table_sha256: str) -> str:
    """The provenance sidecar's accession, or ValueAccessError."""
    if not isinstance(provenance, dict) or tuple(sorted(provenance)) != tuple(
        sorted(PROVENANCE_COLUMNS)
    ):
        raise ValueAccessError(f"provenance must hold exactly {PROVENANCE_COLUMNS}")
    accession = provenance["source_accession"]
    if (
        not isinstance(accession, str)
        or not accession
        or names_adoc_accession(accession)
    ):
        raise ValueAccessError(f"{accession!r} is not an independent accession")
    if provenance["per_cell_table_sha256"] != table_sha256:
        raise ValueAccessError("the provenance does not bind this per-cell table")
    files = provenance["input_files"]
    if not isinstance(files, list) or not files:
        raise ValueAccessError("the provenance names no input FASTQ")
    adoc = adoc_fastq_md5s()
    for entry in files:
        if not isinstance(entry, dict) or set(entry) != {
            "name",
            "md5",
            "published_md5",
        }:
            raise ValueAccessError(
                "each input file needs exactly name, md5, published_md5"
            )
        name = entry["name"]
        if not isinstance(name, str) or not name or ascii_form(name) != name:
            raise ValueAccessError(
                f"input file name {name!r} must be non-empty ASCII text"
            )
        md5, published = str(entry["md5"]), str(entry["published_md5"])
        if not (_MD5.fullmatch(md5) and md5 == published):
            raise ValueAccessError(f"{entry['name']}: md5 does not match the archive's")
        if (
            md5 in adoc
            or names_adoc_donor(entry["name"])
            or names_adoc_accession(entry["name"])
        ):
            raise ValueAccessError(f"{entry['name']} is an ADOC FASTQ")
    return accession


def _number(text: str | None, what: str) -> float:
    if text is None or not _NUMBER.fullmatch(text):
        raise ValueAccessError(f"{what} {text!r} is not a plain non-negative decimal")
    value = float(text)
    if not math.isfinite(value):
        raise ValueAccessError(f"{what} {text!r} is not finite")
    return value


def parse_per_cell(raw: bytes) -> list[DonorCells]:
    reader = csv.reader(io.StringIO(raw.decode("utf-8")), delimiter="\t")
    header = next(reader, None)
    if tuple(header or ()) != PER_CELL_COLUMNS:
        raise ValueAccessError(f"per-cell columns must be exactly {PER_CELL_COLUMNS}")
    grouped: dict[str, tuple[str, list[float], list[float]]] = {}
    for line, row in enumerate(reader, start=2):
        if len(row) != len(PER_CELL_COLUMNS):
            raise ValueAccessError(f"line {line} has {len(row)} fields")
        donor, count, depth = row
        try:
            key = donor_key(donor)
        except IdentityError as refused:
            raise ValueAccessError(str(refused)) from refused
        first, counts, depths = grouped.setdefault(key, (donor, [], []))
        if donor != first:
            raise ValueAccessError(
                f"{donor!r} and {first!r} are one donor spelled twice"
            )
        count_value = _number(count, "klf12_count")
        depth_value = _number(depth, "depth")
        if not depth_value > 0:
            raise ValueAccessError(f"line {line}: depth must be positive")
        if count_value > depth_value * (1.0 + COUNT_DEPTH_TOLERANCE):
            raise ValueAccessError(
                f"line {line}: klf12_count {count} exceeds the cell's depth {depth}"
            )
        counts.append(count_value)
        depths.append(depth_value)
    if not grouped:
        raise ValueAccessError("the per-cell table has no cells")
    return [DonorCells(d, tuple(c), tuple(x)) for d, c, x in sorted(grouped.values())]


def open_reference_values(
    root: Path, path: Path, declared_sha256: str, provenance_path: Path
) -> tuple[dict[str, str], str, list[DonorCells]]:
    """The frozen-rules proof, the accession and the per-donor cells, or an exception."""
    proof = assert_rules_frozen(root)
    root = root.resolve()
    raw = _inside(root, path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != declared_sha256:
        raise ValueAccessError(f"{path} does not hash to the declared sha256")
    if digest in forbidden_reference_shas(root):
        raise ValueAccessError(f"{path} is an ADOC object or a data/ file")
    provenance = json.loads(
        _inside(root, provenance_path).read_text(encoding="utf-8"),
        object_pairs_hook=_no_duplicate_keys,
    )
    accession = check_provenance(provenance, digest)
    return proof, accession, parse_per_cell(raw)
