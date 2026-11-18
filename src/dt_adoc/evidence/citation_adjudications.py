"""Per-relation citation directives for the assertion generator.

``context/evidence-register.tsv`` keys its bibliography by *topic*, and
``migrate_edge_evidence`` fans a topic's whole ``location`` list onto every edge
citing it. A topic is not a citation unit: ``LIT-SPP1-001`` lists five references
and is cited by twelve edges, so Apparao 2001 and Fazleabas 1997 -- neither of
which contains the string "LIF" -- ended up asserted on ``LE017``
(``E_LIF -> E_ITGAVB3_5``). The register cannot fix this, because ``LE017`` and
``LE018`` cite the same topic and need different subsets of it.

This registry supplies the missing ``(edge_id, reference_id)`` granularity as
dated data rather than code, and never edits ``edge_evidence.tsv`` or the
``immutable_parent`` it inherits from. It deliberately mirrors
``config/topology_parity_exemptions.tsv``: rationale, date, and staleness
detection in both directions, so a directive that stops corresponding to a real
defect fails the build instead of silently outliving its repair.

A retraction may not rest on metadata. ``basis`` has no metadata-only value, so a
scope mismatch inferred from a title and abstract can be recorded as a suspicion
on the assertion but can never delete a citation. That is the enforced form of
the distinction between a confirmed and a merely probable misattribution.
"""

from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from pathlib import Path

ADJUDICATION_COLUMNS = (
    "adjudication_id",
    "edge_id",
    "reference_id",
    "action",
    "basis",
    "claim",
    "rationale",
    "action_required",
    "dated",
)

ACTION_VALUES = ("retract", "attach")

#: Bases that may delete a citation. Every one requires the full text: a scope
#: mismatch read off metadata is a suspicion, not a finding.
FULL_TEXT_BASES = (
    "full_text_absence",
    "full_text_contradiction",
    "full_text_scope_mismatch",
)

BASIS_VALUES = (*FULL_TEXT_BASES, "reference_not_in_topic_set")

REQUIRED_BASIS = {
    "retract": FULL_TEXT_BASES,
    "attach": ("reference_not_in_topic_set",),
}


class CitationAdjudicationError(RuntimeError):
    """A citation directive is malformed, duplicated, or no longer applies."""


def load_citation_adjudications(
    path: Path,
    edge_ids: Sequence[str],
    reference_ids: Sequence[str],
) -> list[dict[str, str]]:
    """Load and fully validate the registry. Returns [] when the file is absent."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing = sorted(set(ADJUDICATION_COLUMNS) - set(reader.fieldnames or ()))
        if missing:
            raise CitationAdjudicationError(f"{path} is missing columns: {missing}")
        rows = list(reader)

    known_edges = set(edge_ids)
    known_references = set(reference_ids)
    seen_ids: set[str] = set()
    seen_keys: set[tuple[str, str, str]] = set()
    errors: list[str] = []

    for row in rows:
        identifier = row["adjudication_id"].strip()
        if not identifier or identifier in seen_ids:
            errors.append(f"adjudication_id {identifier!r} is empty or duplicated")
        seen_ids.add(identifier)

        action = row["action"].strip()
        basis = row["basis"].strip()
        if action not in ACTION_VALUES:
            errors.append(f"{identifier} has unknown action {action!r}")
            continue
        if basis not in REQUIRED_BASIS[action]:
            errors.append(
                f"{identifier} has action {action!r} with basis {basis!r}; "
                f"allowed: {list(REQUIRED_BASIS[action])}"
            )
        if row["edge_id"] not in known_edges:
            errors.append(f"{identifier} names unknown edge_id {row['edge_id']!r}")
        if row["reference_id"].strip() not in known_references:
            errors.append(
                f"{identifier} names unknown reference_id {row['reference_id']!r}"
            )
        for field in ("claim", "rationale", "dated"):
            if not row[field].strip():
                errors.append(f"{identifier} is missing {field}")

        key = (row["edge_id"], row["reference_id"].strip(), action)
        if key in seen_keys:
            errors.append(f"{identifier} duplicates an earlier directive for {key}")
        seen_keys.add(key)

    if errors:
        raise CitationAdjudicationError("; ".join(errors))
    return rows


def partition(
    adjudications: Sequence[Mapping[str, str]],
) -> tuple[set[tuple[str, str]], dict[str, list[str]]]:
    """Split directives into ``(retracted_pairs, attachments_by_edge)``."""
    retracted: set[tuple[str, str]] = set()
    attachments: dict[str, list[str]] = {}
    for row in adjudications:
        if row["action"] == "retract":
            retracted.add((row["edge_id"], row["reference_id"]))
        else:
            attachments.setdefault(row["edge_id"], []).append(row["reference_id"])
    return retracted, attachments


def check_applicability(
    adjudications: Sequence[Mapping[str, str]],
    baseline: Mapping[str, Sequence[str]],
) -> None:
    """Fail on directives that no longer correspond to a real defect.

    ``baseline`` is the unmodified topic fan-out, ``{edge_id: [reference_id]}``.
    Staleness is checked in both directions: a retraction of something the
    register no longer provides is as dead as an attachment of something it
    already does.
    """
    errors: list[str] = []
    for row in adjudications:
        present = row["reference_id"] in baseline.get(row["edge_id"], ())
        if row["action"] == "retract" and not present:
            errors.append(
                f"{row['adjudication_id']} retracts {row['reference_id']} from "
                f"{row['edge_id']}, which the register no longer fans out; "
                "delete the directive"
            )
        if row["action"] == "attach" and present:
            errors.append(
                f"{row['adjudication_id']} attaches {row['reference_id']} to "
                f"{row['edge_id']}, which the register already provides; "
                "delete the directive"
            )
    if errors:
        raise CitationAdjudicationError("; ".join(errors))


def load_with_addenda(
    frozen_path: Path,
    addendum_paths: Sequence[Path],
    edge_ids: Sequence[str],
    reference_ids: Sequence[str],
) -> list[dict[str, str]]:
    """Load the frozen registry plus later addenda, as one validated sequence.

    ``config/edge_citation_adjudications.tsv`` is frozen by the Phase 2B
    closure: ``closure_replay.undeclared_drift`` reports any change to it, and
    the historical v0.3.0 generator in ``dt_adoc.evidence.assertions`` replays
    against it byte for byte. Appending to it therefore does two wrong things
    at once -- it breaks the closure guarantee, and it silently rewrites what
    the *historical* migration produces, because that generator reads the same
    file.

    Later adjudications live in their own dated files instead, and only the
    current pipeline reads them. The historical path is left alone, which is
    the point: a citation decided in November 2026 is not part of what the
    v0.3.0 migration did.

    Each file is validated on its own by ``load_citation_adjudications``, and
    then the combination is validated, because the per-file checks cannot see
    across files. ``check_applicability`` is the caller's job, as before, and
    must be given the combined result.
    """
    combined: list[dict[str, str]] = []
    origin: dict[int, Path] = {}
    for path in (frozen_path, *addendum_paths):
        rows = load_citation_adjudications(path, edge_ids, reference_ids)
        for row in rows:
            origin[id(row)] = path
        combined.extend(rows)

    errors: list[str] = []
    seen_ids: dict[str, Path] = {}
    seen_keys: dict[tuple[str, str, str], Path] = {}
    by_pair: dict[tuple[str, str], set[str]] = {}

    for row in combined:
        where = origin[id(row)]
        identifier = row["adjudication_id"].strip()
        if identifier in seen_ids:
            errors.append(
                f"adjudication_id {identifier!r} appears in both "
                f"{seen_ids[identifier]} and {where}; ids are global"
            )
        seen_ids[identifier] = where

        pair = (row["edge_id"], row["reference_id"].strip())
        key = (*pair, row["action"].strip())
        if key in seen_keys:
            errors.append(
                f"{identifier} registers {pair} as {row['action']!r} again; "
                f"already directed in {seen_keys[key]}"
            )
        seen_keys[key] = where
        by_pair.setdefault(pair, set()).add(row["action"].strip())

    # A pair cannot be both attached and retracted. Within one file this is
    # already impossible via check_applicability -- a retraction requires the
    # register to provide the pair and an attachment requires that it does not
    # -- but across files nothing had checked it, and the two directives would
    # have silently raced in `partition`.
    for pair, actions in sorted(by_pair.items()):
        if len(actions) > 1:
            errors.append(
                f"{pair[0]}/{pair[1]} is directed both "
                f"{' and '.join(sorted(actions))}; a citation cannot be "
                "attached and retracted at once"
            )

    if errors:
        raise CitationAdjudicationError("; ".join(errors))
    return combined
