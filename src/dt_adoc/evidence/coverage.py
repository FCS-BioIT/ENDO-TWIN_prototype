"""Per-edge literature coverage, derived rather than remembered.

The 2026-11-18 audit found 47 rows of the previous coverage table still calling
recovered publications abstract-only. The table had been written once, beside a
bundle, and then carried forward while the inventory under it was replaced. The
defect was not arithmetic: the generator had no way to say which availability
snapshot it had used, so nothing could notice that the snapshot had moved on.

Two decisions here follow from that.

Availability is an *argument*, never a default. ``build_coverage`` takes the
``{reference_id: availability}`` mapping it is to use and will not look one up
on its own, so a caller cannot accidentally reuse last week's. And the mapping
it was given is fingerprinted into the report, so a row and the snapshot that
produced it travel together and a stale pairing is visible rather than implied.

The second is that a reference the mapping does not mention is `unknown`, not
`abstract_only`. Silence about a publication is not a claim that it is
unavailable, and the previous table's whole failure mode was treating one as
the other.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from dt_adoc.evidence import experimental as ex

#: Availability states a reference may carry. `complete` means the full article
#: is held; `abstract_only` that just an abstract is; `unknown` that the
#: snapshot does not say, which is a third thing and must not collapse into the
#: second.
AVAILABILITY_VALUES = ("complete", "abstract_only", "unavailable", "unknown")

COVERAGE_COLUMNS = (
    "edge_id",
    "source",
    "target",
    "sign",
    "edge_status",
    "edge_role",
    "evidence_records",
    "records_graded",
    "references_cited",
    "references_with_full_text",
    "references_abstract_only",
    "references_unknown_availability",
    "in_house_observations",
    "coverage",
)


class CoverageError(RuntimeError):
    """The coverage inputs are inconsistent or incomplete."""


@dataclass(frozen=True)
class CoverageReport:
    rows: tuple[dict[str, str], ...]
    #: Fingerprint of the availability mapping actually used.
    availability_sha256: str
    availability_count: int
    model_version: str
    inputs: dict[str, str] = field(default_factory=dict)


def fingerprint_availability(availability: Mapping[str, str]) -> str:
    """A stable digest of the availability snapshot, for provenance."""
    body = "\n".join(f"{ref}\t{availability[ref]}" for ref in sorted(availability))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _coverage_label(
    cited: Sequence[str],
    full: Sequence[str],
    unknown: Sequence[str],
    in_house: Sequence[str],
) -> str:
    if not cited:
        return "in_house_evidence_only" if in_house else "no_evidence"
    if unknown:
        # Not 'partly_available': we do not know that the rest is missing.
        return (
            "availability_unknown" if len(unknown) == len(cited) else "partly_unknown"
        )
    if len(full) == len(cited):
        return "fully_available"
    if full:
        return "partly_available"
    return "none_available"


def build_coverage(
    availability: Mapping[str, str],
    *,
    model_version: str = ex.DEFAULT_MODEL_VERSION,
    root: Path | None = None,
    inputs: Mapping[str, str] | None = None,
) -> CoverageReport:
    """Build the per-edge coverage table against an explicit availability map.

    ``availability`` is required and is not defaulted from any file on disk:
    that is the whole point. Passing a snapshot makes the caller say which one.
    """
    unknown_states = sorted(set(availability.values()) - set(AVAILABILITY_VALUES))
    if unknown_states:
        raise CoverageError(
            f"availability values outside {list(AVAILABILITY_VALUES)}: {unknown_states}"
        )

    root = root or ex.repo_root()
    contexts = ex.edge_context(model_version, root)
    roles = ex.load_roles(root)
    table = ex.read_tsv(root / ex.EVIDENCE_TABLE_PATH)

    by_edge: dict[str, list[dict[str, str]]] = {}
    for row in table:
        by_edge.setdefault(row["edge_id"], []).append(row)

    rows: list[dict[str, str]] = []
    for edge_id, context in contexts.items():
        records = by_edge.get(edge_id, [])
        cited = sorted({r["reference_id"] for r in records if r["reference_id"]})
        in_house = sorted(
            {r["source_observation_id"] for r in records if r["source_observation_id"]}
        )
        full = [r for r in cited if availability.get(r, "unknown") == "complete"]
        abstract = [
            r for r in cited if availability.get(r, "unknown") == "abstract_only"
        ]
        unknown = [
            r
            for r in cited
            if availability.get(r, "unknown") in ("unknown", "unavailable")
        ]
        graded = [r for r in records if r["curation_status"] != "unreviewed"]
        rows.append(
            {
                "edge_id": edge_id,
                "source": context.source,
                "target": context.target,
                "sign": context.sign,
                "edge_status": context.edge_status,
                "edge_role": roles.get(edge_id, {}).get("edge_role", ""),
                "evidence_records": str(len(records)),
                "records_graded": str(len(graded)),
                "references_cited": ";".join(cited),
                "references_with_full_text": ";".join(full),
                "references_abstract_only": ";".join(abstract),
                "references_unknown_availability": ";".join(unknown),
                "in_house_observations": ";".join(in_house),
                "coverage": _coverage_label(cited, full, unknown, in_house),
            }
        )

    rows.sort(key=lambda r: ex._natural_edge_key(r["edge_id"]))
    return CoverageReport(
        rows=tuple(rows),
        availability_sha256=fingerprint_availability(availability),
        availability_count=len(availability),
        model_version=model_version,
        inputs=dict(inputs or {}),
    )


def availability_from_inventory(path: Path) -> dict[str, str]:
    """Read a packaged ``literature_inventory.tsv`` into an availability map.

    The inventory's own vocabulary is passed through unchanged where it is one
    of ours, and anything else becomes `unknown` rather than being guessed into
    a state it may not mean.
    """
    mapping: dict[str, str] = {}
    for row in ex.read_tsv(path):
        state = row.get("availability", "").strip()
        mapping[row["reference_id"]] = (
            state if state in AVAILABILITY_VALUES else "unknown"
        )
    return mapping


def stale_rows(report: CoverageReport, availability: Mapping[str, str]) -> list[str]:
    """Rows contradicted by ``availability``: the exact defect the audit found.

    A row is stale when it calls a reference abstract-only (or leaves its
    availability unknown) that the given snapshot says is complete.
    """
    complete = {ref for ref, state in availability.items() if state == "complete"}
    stale = []
    for row in report.rows:
        wrong = sorted(
            set(
                ex._tokens(row["references_abstract_only"])
                + ex._tokens(row["references_unknown_availability"])
            )
            & complete
        )
        if wrong:
            stale.append(f"{row['edge_id']}: {';'.join(wrong)} are full text")
    return stale


# --------------------------------------------------------------------------
# Per-edge evidence summary
# --------------------------------------------------------------------------
#
# This is deliberately NOT an edge-level grade.
#
# Section 7.1 of docs/evidence_grading.md specifies edge-level aggregation, and
# it is more than a fold over rows: a contradiction counts only when its
# strength is `strong` or `moderate`, its weight is compared against the base
# grade, a lighter one downgrades by one level and flags the edge `contested`
# rather than overturning it, replication promotes only under four conjoined
# conditions, and every grade carries a curation-completeness label.
#
# An earlier version of this module set `contradicted` whenever any examined row
# carried `edge_support='contradictory'`. That is wrong on the rubric's own
# terms -- strong positive evidence beside one weak contradictory observation is
# not a contradicted edge -- and wrong in a way that is hard to see, because the
# output looked like a grade and would have been read as one.
#
# So no grade is emitted. What follows is a description: who supports, who
# contradicts, how credible each contradiction is, and how much of the edge has
# been read at all. Section 7.1 stays unimplemented until it is implemented
# whole, which is also a decision the owner has not yet reviewed.

#: How much of an edge's evidence has been examined. This is about reading,
#: not about what the reading found.
COVERAGE_STATES = (
    "no_evidence",  # nothing cited and nothing observed in house
    "unassessed",  # rows exist, none examined
    "partially_examined",  # some examined, some still unreviewed
    "examined",  # every row examined
)

#: Strengths at which the rubric lets a contradiction count at all (7.1 step 3).
CREDIBLE_CONTRADICTION_STRENGTHS = ("strong", "moderate")

#: Confidences at which a direct or partial row counts as support (7.1 step 3,
#: the other half of the same sentence). `unsupported` and `unassessed` do not:
#: a row can carry `direct` support and still reach no confidence at all.
SUPPORTING_CONFIDENCES = ("high", "medium", "low")


@dataclass(frozen=True)
class Contradiction:
    """One examined row whose result opposes the encoded relation."""

    evidence_piece_id: str
    experimental_strength: str
    human_ADOC_relevance: str
    #: Does it clear the rubric's credibility bar (7.1 step 3)?
    credible: bool
    #: What it would have weighed had it supported the edge (7.1 step 3).
    weight: str


@dataclass(frozen=True)
class EdgeEvidenceSummary:
    """What is known about one edge. Not a grade, and no field is one."""

    edge_id: str
    coverage: str
    #: `complete` when nothing is left unreviewed, else `partial`, else `none`.
    curation_completeness: str

    supporting_pieces: tuple[str, ...]
    #: Best `overall_confidence` among supporting rows. Every graded row in the
    #: table is provisional today, so this is a provisional figure.
    best_supporting_confidence: str
    independent_supporting_groups: int
    any_supporting_verified: bool

    contradictions: tuple[Contradiction, ...]
    #: Pieces recording that a citation does not test this relation. These are
    #: NOT contradictions: the publication is silent about the edge, which is
    #: not the same as opposing it, and conflating them would turn a gap in the
    #: literature into negative evidence.
    not_demonstrated_pieces: tuple[str, ...]

    unreviewed_pieces: tuple[str, ...]

    @property
    def credible_contradictions(self) -> tuple[Contradiction, ...]:
        return tuple(c for c in self.contradictions if c.credible)

    @property
    def competing_positive_evidence(self) -> bool:
        """Is there supporting evidence for a contradiction to be weighed
        against? Step 6 of the rubric needs this and step 4 branches on it."""
        return bool(self.supporting_pieces)


class FilterRefused(RuntimeError):
    """A filtered network was requested that the evidence cannot justify."""


def edge_evidence_summary(
    *, model_version: str = ex.DEFAULT_MODEL_VERSION, root: Path | None = None
) -> dict[str, EdgeEvidenceSummary]:
    """Describe each edge's evidence without grading it."""
    root = root or ex.repo_root()
    contexts = ex.edge_context(model_version, root)
    table = ex.read_tsv(root / ex.EVIDENCE_TABLE_PATH)
    return summarize_rows_by_edge(table, edges=contexts)


def summarize_rows_by_edge(
    rows: Sequence[Mapping[str, str]],
    *,
    edges: Mapping[str, object] | None = None,
) -> dict[str, EdgeEvidenceSummary]:
    """The summary, over supplied rows.

    Separated from the repository lookup so that tests can exercise it with
    synthetic evidence sets rather than with whatever the table happens to hold
    today -- the distribution of grades in the live table is thin and changes,
    and a rule tested only against it would be tested against one sample.
    """
    by_edge: dict[str, list[Mapping[str, str]]] = {e: [] for e in (edges or {})}
    for row in rows:
        by_edge.setdefault(row["edge_id"], []).append(row)

    out: dict[str, EdgeEvidenceSummary] = {}
    for edge_id, edge_rows in by_edge.items():
        examined = [r for r in edge_rows if r.get("curation_status") != "unreviewed"]
        unreviewed = tuple(
            r["evidence_piece_id"]
            for r in edge_rows
            if r.get("curation_status") == "unreviewed"
        )
        # Section 7.1 step 3 defines a supporting piece by BOTH halves of one
        # sentence: `edge_support` direct or partial *and* `overall_confidence`
        # high, medium or low. Filtering on support alone let a row through
        # that the rubric does not count -- `direct` support with
        # `overall_confidence='unsupported'` is validator-legal, because a
        # direct perturbation whose `experimental_strength` is `insufficient`
        # has a ceiling of `unsupported`. Such a row was reported as support
        # with a "best supporting confidence" of `unsupported`, which is a
        # contradiction in terms, and it set `competing_positive_evidence`
        # True for an edge that on the rubric has no positive evidence at all.
        # No row in the table triggers it today; that is not a reason to keep
        # half a definition.
        supporting = [
            r
            for r in examined
            if r.get("edge_support") in ("direct", "partial")
            and r.get("overall_confidence") in SUPPORTING_CONFIDENCES
        ]
        contradicting = [
            r for r in examined if r.get("edge_support") == "contradictory"
        ]
        not_demonstrated = tuple(
            r["evidence_piece_id"]
            for r in examined
            if r.get("edge_support") == "not_demonstrated"
        )

        if not edge_rows:
            coverage = "no_evidence"
        elif not examined:
            coverage = "unassessed"
        elif unreviewed:
            coverage = "partially_examined"
        else:
            coverage = "examined"

        completeness = (
            "none" if not edge_rows else "partial" if unreviewed else "complete"
        )

        best = "unassessed"
        for row in supporting:
            if ex.CONFIDENCE_RANK[row["overall_confidence"]] > ex.CONFIDENCE_RANK[best]:
                best = row["overall_confidence"]

        out[edge_id] = EdgeEvidenceSummary(
            edge_id=edge_id,
            coverage=coverage,
            curation_completeness=completeness,
            supporting_pieces=tuple(r["evidence_piece_id"] for r in supporting),
            best_supporting_confidence=best,
            independent_supporting_groups=len(
                {
                    r["independence_group"]
                    for r in supporting
                    if r.get("independence_group")
                }
            ),
            any_supporting_verified=any(
                r.get("curation_status") == "verified" for r in supporting
            ),
            contradictions=tuple(
                Contradiction(
                    evidence_piece_id=r["evidence_piece_id"],
                    experimental_strength=r.get("experimental_strength", ""),
                    human_ADOC_relevance=r.get("human_ADOC_relevance", ""),
                    credible=r.get("experimental_strength")
                    in CREDIBLE_CONTRADICTION_STRENGTHS,
                    weight=ex.contradiction_weight(
                        r.get("experimental_strength", ""),
                        r.get("human_ADOC_relevance", ""),
                    ),
                )
                for r in contradicting
            ),
            not_demonstrated_pieces=not_demonstrated,
            unreviewed_pieces=unreviewed,
        )
    return out


def refuse_filter_if_premature(
    summaries: Mapping[str, EdgeEvidenceSummary], level: str
) -> None:
    """Refuse `high`/`high_medium` filtering while the evidence cannot bear it.

    A filtered network presented as validated biology is a stronger claim than
    the evidence behind it, and the failure mode is silent. `all` is always
    allowed because it asserts nothing.

    No Boolean rule filtering is implemented. There is deliberately nothing
    here that edits `network.bnd`: section 7.2 requires a parsed rule tree with
    byte-identical re-rendering of the rules that did not change, and with no
    edge-level grade to filter on there is nothing for it to keep. A rule
    rewriter that cannot be exercised is a liability rather than infrastructure.
    """
    if level == "all":
        return
    if level not in ("high", "high_medium"):
        raise FilterRefused(f"unknown filter level {level!r}")
    verified = [s for s in summaries.values() if s.any_supporting_verified]
    unassessed = [s for s in summaries.values() if s.coverage == "unassessed"]
    partial = [s for s in summaries.values() if s.coverage == "partially_examined"]
    raise FilterRefused(
        f"{level!r} filtering is refused: no edge-level grade exists, "
        f"{len(verified)} edges have a verified supporting record, "
        f"{len(unassessed)} have no examined record at all and "
        f"{len(partial)} are only partly examined. Filtering now would read an "
        "unexamined edge as an unsupported one, which is the inference "
        "docs/evidence_grading.md forbids. Section 7.1 aggregation is "
        "unimplemented; see docs/scientific_review_2026-11-18/README.md."
    )
