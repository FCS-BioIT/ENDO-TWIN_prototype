"""Phase 2B: identity checks that no spelling can slip past.

Phase 2A's `is_adoc_donor` / `is_adoc_citation` drop non-ASCII characters and
then look for a substring, so a full-width, Arabic-Indic or Cyrillic look-alike
of `SZ09`, or `SZ9` / `SZ009`, is not recognised. Phase 2A is not repaired
here. Phase 2B applies these stricter checks in addition to it:

- text is NFKC-normalised first, which maps full-width and other compatibility
  forms to ASCII;
- anything still non-ASCII after that is refused outright, so a confusable
  cannot pass as a different id;
- ADOC donors are matched as `SZ` (or `5`/`2` look-alikes), any leading
  zeros, then 9, 10 or 25, with O, I and l read as 0, 1 and 1, both with
  separators removed and token by token;
- ADOC accessions are matched against `adoc_identity_denylist.json`, which
  holds E-MTAB-15842 and every ENA study, run, experiment and sample id of
  it, with the same look-alike fold and leading zeros stripped from each
  digit run.

A donor id must be `[A-Za-z0-9][A-Za-z0-9_.-]*`, and two ids that differ only
in case are one donor.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import cache
from pathlib import Path

from dt_adoc.personalization.phase2a_contract import is_adoc_citation, is_adoc_donor

DENYLIST = (
    Path(__file__).resolve().parents[4] / "docs/phase2b/adoc_identity_denylist.json"
)
DONOR_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")
_ADOC_DONOR = re.compile(r"[S5][Z2]0*(?:9|10|25)(?![0-9])")


class IdentityError(ValueError):
    pass


def ascii_form(value: object) -> str | None:
    """NFKC-normalised text if it is pure ASCII, else None."""
    text = unicodedata.normalize("NFKC", str(value))
    return text if text.isascii() else None


#: Look-alike glyphs read as the digit they resemble. Applied identically to
#: the probe and to every deny-list entry, so it can only widen a match.
_DIGIT_LOOKALIKES = str.maketrans({"O": "0", "I": "1", "L": "1"})


def _folded(text: str) -> str:
    """Upper case, look-alike digits folded, separators removed."""
    return re.sub(r"[^A-Z0-9]", "", text.upper().translate(_DIGIT_LOOKALIKES))


def _tokens(text: str) -> list[str]:
    """Upper case, look-alike digits folded, split on every separator."""
    return [
        t
        for t in re.split(r"[^A-Z0-9]+", text.upper().translate(_DIGIT_LOOKALIKES))
        if t
    ]


def _strip_zeros(text: str) -> str:
    return re.sub(r"[0-9]+", lambda m: m.group(0).lstrip("0") or "0", text)


@cache
def denylist() -> dict[str, object]:
    return json.loads(DENYLIST.read_text(encoding="utf-8"))


def names_adoc_donor(value: object) -> bool:
    """True for any spelling of an ADOC donor, and for anything non-ASCII."""
    text = ascii_form(value)
    if text is None:
        return True
    # Two readings, either of which refuses: separators removed (catches
    # "S Z 0 9"), and each separator-delimited token on its own (catches
    # "SZ9_2", where removing the separator would glue on another digit).
    return (
        is_adoc_donor(text)
        or bool(_ADOC_DONOR.search(_folded(text)))
        or any(_ADOC_DONOR.match(token) for token in _tokens(text))
    )


def names_adoc_accession(value: object) -> bool:
    """True for any spelling of an ADOC accession or ENA id, and for anything non-ASCII."""
    text = ascii_form(value)
    if text is None:
        return True
    if is_adoc_citation(text):
        return True
    probe = _strip_zeros(_folded(text))
    return any(_strip_zeros(_folded(str(a))) in probe for a in denylist()["accessions"])


def adoc_fastq_md5s() -> frozenset[str]:
    return frozenset(str(e["md5"]).lower() for e in denylist()["fastq_submitted_md5"])


def donor_key(value: object) -> str:
    """The canonical key of a reference donor id, or IdentityError."""
    if not isinstance(value, str) or not DONOR_ID.fullmatch(value):
        raise IdentityError(f"donor id {value!r} must match {DONOR_ID.pattern}")
    if names_adoc_donor(value):
        raise IdentityError(f"{value!r} names an ADOC donor; never a reference donor")
    return value.casefold()
