"""The staged deep-research bundle must stay quarantined and stay verbatim.

`context/literature/staging/deep_research_adhesion_model_2026-09-11/` is external
candidate evidence, not accepted biology. Four of its rows are adjudicated
`blocks_promotion=yes` and are deliberately left broken in place: repairing them
would destroy the record of what the external reviewer actually sent, and
`AGENTS.md` requires raw and derived stages to stay separate.

That decision is only defensible while one invariant holds: **the biology in a
blocking row cannot reach a canonical literature table or an executable model.**
The repository asserted that invariant to its reviewer and called it checkable,
but committed no check, so nothing would notice if a later promotion pass merged
one. Prose is not a gate. This module is.

**What "cannot reach" means here, and what it does not.** An earlier revision of
this module searched canonical artifacts for the staged *identifier* only. That
is too weak to enforce the invariant it claimed: promotion renames rows, and
compiling a rule variant into a `.bnd` drops identifiers entirely, so a blocking
row could be promoted under a new id and pass. The checks below are therefore on
**content** -- an edge's `(source, target)` pair, a rule variant's
`(node_id, expression)` -- plus the identifier and the preserved provenance link,
each of which fails independently.

A fourth check enforces that promotion **consults the adjudication** rather than
merely dodging the ids that block today. The repository already carries a
`source_table` / `source_row_id` provenance convention across its model tables,
so any row declaring this bundle as its source must name a staged row that was
actually adjudicated, and that decision must not block. A row promoted out of the
bundle with no adjudication entry is a leak even though it matches no blocking id
and carries no blocking content. There is no *code* promotion path to gate --
nothing has been promoted, and `promotion_plan.tsv` describes intended future
actions rather than an implemented mechanism -- so the artifact surface is the
only surface that exists to enforce, and this enforces it. When a promotion tool
is built it must satisfy this same check, because the rows it writes are what the
check reads.

**Blocked is decided by the adjudication, not by the id.** DRE009's decision is
`REJECT_CONFIDENCE_LABEL`: it rejects a LABEL, not the biology, and explicitly
leaves the edge admissible once downgraded. So every detector that reads a
confidence-bearing row asks `_promotion_is_blocked`, and a row that honestly
declares `source_table`/`source_row_id`, promotes at a permitted label, and
carries the content that decision actually read is not reported merely for
naming that id. All three conditions, because **a citation is checked, not
believed**: the first version of this repair granted the waiver on the id and
the label alone, and an independent review planted an unrelated edge and a
sign-reversed one under a `DRE009` citation and watched the gate pass both. A
promotion that transforms the biology instead of downgrading its label -- the
abundance-state redefinition DRE009's basis also leaves open -- changes what was
adjudicated and needs a new decision; see
`_promotion_carries_the_adjudicated_content`.

An earlier revision got the permission backwards in a
way its own tests could not see: the policy function permitted the downgrade
while the identifier scan, the provenance-link check and the adjudication check
each refused any row mentioning a blocking id, and the tests for the permitted
labels omitted the provenance columns, so they exercised a promotion shape no
real promotion would take. Declaring provenance must not be the thing that makes
a permitted promotion fail, or the gate teaches promotions to hide where they
came from.

The honest residual limit: a promoted expression that has been *semantically
rewritten* -- terms reordered, or rebuilt through an equivalent gate -- would
defeat the normalised comparison, because deciding that is Boolean equivalence
and not a string test. Expressions are normalised for whitespace and case only.
So this module enforces that a blocking row cannot be promoted *as written*,
renamed, reformatted or compiled; it does not certify that no equivalent biology
was reintroduced from scratch. Promotion still requires overturning the
adjudication decision, which is the reviewable step.

Each check is a function of a repository root so the negative controls can run
it against a planted tree; a gate nobody has watched fail is not known to work.
"""

from __future__ import annotations

import csv
import hashlib
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = "deep_research_adhesion_model_2026-09-11"
STAGING_RELATIVE = Path("context") / "literature" / "staging" / BUNDLE
ADJUDICATION_RELATIVE = (
    Path("context") / "literature" / "reviews" / f"{BUNDLE}.adjudication.tsv"
)

#: Tables a promotion would land in. Everything under `models/` is in scope:
#: a blocking row reaching *any* model version is a promotion, not just one
#: reaching the version currently built.
SCANNED_ROOTS = (Path("models"), Path("context") / "literature", Path("config"))
SCANNED_SUFFIXES = {".tsv", ".yaml", ".toml", ".bnd", ".cfg"}

#: Excluded from the scan, because these ARE the quarantine record rather than
#: somewhere a promotion could land. `staging/` is the verbatim bundle, and
#: `reviews/` is the derived adjudication layer whose whole job is to name the
#: blocking rows and say why they are blocked -- `promotion_plan.tsv` classes the
#: only file copied there as "provenance only". Scanning either would make the
#: gate fire on the record of the decision it is enforcing.
EXCLUDED_DIRS = (
    Path("context") / "literature" / "staging",
    Path("context") / "literature" / "reviews",
)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _raw_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    """Header cells and every data row's cells, exactly as written.

    `csv.DictReader` is the right reader for the named-field detectors and the
    wrong one for the identifier scan. A row wider than its header puts the
    extra cells in a LIST under the key `None`, and a duplicated header name
    keeps only the last of its columns -- so a blocking id written into either
    is invisible to anything reading `row[field]`, while a reader opening the
    file sees it. Both are shapes a malformed or deliberately crafted table
    takes, so the identifier scan reads cells rather than fields.
    """
    with path.open(encoding="utf-8", newline="") as handle:
        parsed = list(csv.reader(handle, delimiter="\t"))
    if not parsed:
        return [], []
    return parsed[0], parsed[1:]


def _normalise(expression: str) -> str:
    """Whitespace and case only -- never an equivalence decision.

    Enough to survive reformatting and re-indentation, which is what promotion
    realistically does to an expression. Deliberately not enough to claim a
    semantically rewritten rule would be caught; see the module docstring.
    """
    return re.sub(r"\s+", " ", expression).strip().lower()


def _bnd_logic(text: str) -> dict[str, str]:
    """Node id -> its complete normalised logic expression, from a `.bnd`.

    Only whole assignments, so a rule can be compared for equality rather than
    containment. Nodes without a `logic =` line (pure rate definitions) are
    absent rather than empty, so they cannot accidentally match.
    """
    logic: dict[str, str] = {}
    node: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        match = re.match(r"^Node\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{", stripped)
        if match:
            node = match.group(1)
            continue
        if stripped.startswith("}"):
            node = None
            continue
        if node is None:
            continue
        assignment = re.match(r"^logic\s*=\s*(.+?);\s*$", stripped)
        if assignment:
            expression = assignment.group(1).strip()
            # A whole-expression wrapper adds nothing and would defeat equality.
            while expression.startswith("(") and expression.endswith(")"):
                inner = expression[1:-1]
                if inner.count("(") != inner.count(")"):
                    break
                expression = inner.strip()
            logic[node] = _normalise(expression)
    return logic


def _scanned_files(root: Path) -> list[Path]:
    """Every artifact a promotion could land in, excluding the quarantine record."""
    excluded = [root / relative for relative in EXCLUDED_DIRS]
    found: list[Path] = []
    for scanned in SCANNED_ROOTS:
        base = root / scanned
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in SCANNED_SUFFIXES:
                continue
            if any(one == path.parent or one in path.parents for one in excluded):
                continue
            found.append(path)
    return found


def blocking_rows(root: Path) -> list[dict[str, str]]:
    """Adjudicated rows that block promotion, joined to their staged content."""
    decisions = [
        row
        for row in _rows(root / ADJUDICATION_RELATIVE)
        if row["blocks_promotion"].strip().lower() == "yes"
    ]
    staged_cache: dict[str, list[dict[str, str]]] = {}
    joined: list[dict[str, str]] = []
    for decision in decisions:
        staged_file = decision["staged_file"].strip()
        if staged_file not in staged_cache:
            staged_cache[staged_file] = _rows(root / STAGING_RELATIVE / staged_file)
        first_column = next(iter(staged_cache[staged_file][0]))
        for staged in staged_cache[staged_file]:
            if staged[first_column].strip() == decision["staged_id"].strip():
                joined.append({**staged, "_staged_file": staged_file})
                break
    return joined


def adjudication_index(root: Path) -> dict[str, str]:
    """staged_id -> decision, for every adjudicated row (blocking or not)."""
    return {
        row["staged_id"].strip(): row["decision"].strip()
        for row in _rows(root / ADJUDICATION_RELATIVE)
    }


def _staged_basenames(root: Path) -> set[str]:
    staging = root / STAGING_RELATIVE
    if not staging.is_dir():
        return set()
    return {path.name for path in staging.iterdir() if path.is_file()}


def names_this_bundle(source_table: str, staged_basenames: set[str]) -> bool:
    r"""Does this `source_table` value refer to the staged bundle?

    Must accept every spelling a promoted row could plausibly use, because an
    exact-string test silently accepts the others. The repository's own
    convention is a **repository-relative path** -- `complete_nodes.tsv` already
    carries `context/literature/candidate-nodes.tsv` -- so matching only the
    bundle directory name and the bare staged filenames missed the single most
    likely spelling, `context/literature/staging/<bundle>/edge_evidence.tsv`.

    Recognised: any path with the bundle directory as a segment (at any depth,
    absolute or relative, `/` or `\`), and the bare staged filenames, which is
    how the staged `rule_variants.tsv` rows cite their own bundle.
    """
    value = source_table.strip().replace("\\", "/").strip("/")
    if not value:
        return False
    segments = [segment for segment in value.split("/") if segment not in ("", ".")]
    if BUNDLE in segments:
        return True
    return len(segments) == 1 and segments[0] in staged_basenames


def _identifiers(expression: str) -> set[str]:
    """Node names appearing as terms in a Boolean expression, lowercased.

    Term-level, so `X_IL11` is found inside
    `E_GP130_STAT3 and (X_IL11 or E_SOX17)` but `IL11` alone is not: the pattern
    is anchored on word boundaries, which stops a short node name matching a
    longer one that contains it.
    """
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expression.lower()))


#: Decisions whose promotion is blocked outright, because nothing about the
#: promoted row can satisfy them: the citation does not resolve
#: (`REJECT_PROVENANCE`), or adjudication never reached a conclusion
#: (`UNRESOLVED`). Only `REJECT_CONFIDENCE_LABEL` names a condition a promotion
#: can actually meet, and it is handled separately below.
UNCONDITIONALLY_BLOCKED_DECISIONS = frozenset({"REJECT_PROVENANCE", "UNRESOLVED"})

#: The weaker labels a `REJECT_CONFIDENCE_LABEL` decision admits, ENUMERATED by
#: the adjudicator rather than ordered by this module. DRE009's recorded note
#: reads "Admissible only as candidate/assumption", and that is the whole of the
#: permission. `hypothesis` was in this set and appears nowhere in the record: a
#: reader can call it weaker than `candidate`, but ranking labels the adjudicator
#: did not name is the same substitution of a paraphrase for the decision that
#: this module exists to prevent, made here by the gate itself.
#: `TheAdmissibleLabelsComeFromTheRecord` pins it against the adjudication, so a
#: record that later names a different label fails rather than being silently
#: enforced as this list.
ADMISSIBLE_WEAKER_LABELS = frozenset({"candidate", "assumption"})

#: Every field a waiver is read from -- the citation, the label, and the content
#: compared against the staged row. `csv.DictReader` keeps ONE column per
#: repeated header name and discards the rest, so where any of these is declared
#: twice, which cell a decision was read from is not recoverable and no waiver
#: can be granted from that table. Uniqueness was checked for `source_row_id`
#: alone, which left a shadowed `confidence` or `source` column able to carry
#: one value past the check while the gate read another.
WAIVER_FIELDS = (
    "source_table",
    "source_row_id",
    "confidence",
    "source",
    "target",
    "sign",
    "node_id",
    "expression",
)


def _promotion_is_blocked(
    *, decision: str, staged_confidence: str, promoted_confidence: str
) -> tuple[bool, str]:
    """Does the RECORDED adjudication block this promotion of a staged row?

    This enforces the decision the adjudication actually made, which is not the
    same as banning the edge. An earlier revision of this module did ban it
    outright, and that was wrong in the permissive direction as well as the
    strict one: DRE009's decision is `REJECT_CONFIDENCE_LABEL`, and its recorded
    basis rejects the row for marking an integrin-alpha2 *expression/protein*
    observation as a `verified` receptor-activity edge. What it objects to is the
    CONFIDENCE LABEL on that biological state, and it explicitly leaves the edge
    admissible once downgraded to candidate/assumption. A blanket ban would have
    failed a promotion the record permits, so the gate would have been enforcing
    this module's paraphrase rather than the adjudication.

    The record once read as offering a SECOND route -- promotion at `verified`
    once `E_ITGA2B1` is redefined from a receptor-activity/heterodimer state to
    an abundance state -- and this gate has always refused to infer it, on the
    grounds that redefining the target changes the biological claim adjudicated
    and so needs a fresh decision. That refusal was right and the record now says
    so directly (POLICY CLARIFICATION 2026-09-14 in DRE009's note): the
    redefinition is not a promotion route under this row. The gate is unchanged;
    what closed was the gap between what it enforces and what the record appeared
    to authorise. `TheRedefinitionRouteIsNotAPromotionRoute` pins that alignment
    so the two cannot drift apart again.

    So: `REJECT_CONFIDENCE_LABEL` blocks promotion at the rejected label and
    permits the weaker labels the record NAMES, which for DRE009 are
    `candidate` and `assumption` and nothing else -- see
    `ADMISSIBLE_WEAKER_LABELS`, and note that admitting a label a reader would
    call weaker is the paraphrase, not the enforcement. Every other blocking
    decision admits no weaker form and blocks outright.

    This is the ONLY place that decision is made. Every detector in `leaks` that
    reads a row delegates here, because a detector that reimplements the rule as
    `id in blocking_ids` is back to enforcing this module's paraphrase -- and
    three of them did exactly that, which is why an honest promotion carrying
    `source_table`/`source_row_id` used to be refused at every label while the
    same row without those columns was allowed. Surfaces that cannot express a
    weaker form -- a `.bnd`, a table with no `confidence` column -- pass the
    empty label they have, and are blocked. It decides the LABEL only: whether
    the promoted row is the one the decision was about is a separate question,
    answered by `_promotion_carries_the_adjudicated_content`, and both must pass
    before a promotion is permitted.

    Returns `(blocked, reason)` so the caller can say which rule fired.
    """
    decision = (decision or "").strip().upper()
    if decision in UNCONDITIONALLY_BLOCKED_DECISIONS:
        return True, f"adjudication is {decision}, which admits no promoted form"
    if decision == "REJECT_CONFIDENCE_LABEL":
        if promoted_confidence in ADMISSIBLE_WEAKER_LABELS:
            return False, ""
        return True, (
            f"adjudication rejects the {staged_confidence or 'recorded'!r} "
            "confidence label; promote as candidate/assumption, or redefine the "
            "target node, and re-adjudicate"
        )
    # An unrecognised blocking decision is treated as blocking. A new decision
    # kind must be given semantics here deliberately, not silently permitted.
    return True, f"unrecognised blocking decision {decision!r}"


def _promotion_carries_the_adjudicated_content(
    *, promoted: dict[str, str], staged: dict[str, str], source_table: str
) -> tuple[bool, str]:
    """Does this row promote the staged row it cites, or merely cite it?

    A decision waives what it adjudicated and nothing else. DRE009's
    `REJECT_CONFIDENCE_LABEL` permits ONE edge at a weaker label -- `X_IL11 ->
    E_ITGA2B1`, activating. It says nothing about any other biology, and no
    adjudicator read any other biology. Granting the waiver on the citation id
    and the promoted label alone turns `source_row_id=DRE009` into a laundry
    channel: an unreviewed edge, or this edge with its sign reversed, enters a
    canonical table carrying provenance that is false about precisely the thing
    provenance is for. That is worse than the leak the gate was written to stop,
    because the row looks audited.

    So a waiver requires correspondence: the cited `source_table` must name the
    staged FILE the decision was recorded against, and the promoted row must
    carry the staged row's content -- normalised for case and whitespace only,
    which is what promotion realistically does to it.

    A promotion that genuinely TRANSFORMS the biology is not this case. The
    abundance-state redefinition DRE009's basis also leaves open changes what
    was adjudicated, so it needs a new decision -- which is the reviewable step
    the quarantine exists to force, and not something this gate can infer.
    """
    cited = source_table.strip().replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
    staged_file = staged.get("_staged_file", "")
    if cited != staged_file:
        return False, (
            f"cites source_table={source_table!r}, which does not name "
            f"{staged_file}, the staged file the decision was recorded against"
        )

    def differs(field: str) -> str:
        want = _normalise(staged.get(field) or "")
        got = _normalise(promoted.get(field) or "")
        if want == got:
            return ""
        return f"{field}={got or '<none>'} where the staged row has {want or '<none>'}"

    if "source" in staged and "target" in staged:
        if "source" not in promoted or "target" not in promoted:
            return False, "declares no source/target to compare with the staged edge"
        for field in ("source", "target", "sign"):
            if field not in staged:
                continue
            mismatch = differs(field)
            if mismatch:
                return False, mismatch
        return True, ""
    if "node_id" in staged and "expression" in staged:
        if "node_id" not in promoted or "expression" not in promoted:
            return False, (
                "declares no node_id/expression to compare with the staged rule"
            )
        for field in ("node_id", "expression"):
            mismatch = differs(field)
            if mismatch:
                return False, mismatch
        return True, ""
    return False, "the staged row it cites carries no content this gate can compare"


def leaks(root: Path) -> list[str]:
    """Every way a blocking row is detectably present outside the bundle.

    Four independent detectors, because each defeats a different promotion
    mistake: the identifier catches a copied row, the content catches a renamed
    or compiled one, the provenance link catches a rewritten row that still
    declares where it came from, and the adjudication check catches a row
    promoted out of this bundle that was never adjudicated at all.

    In a `.tsv` the identifier, provenance-link and adjudication detectors are
    decided PER ROW. One cell is exempt from the identifier scan and nothing
    else is: the cell in the row's single `source_row_id` COLUMN, where that row
    cites this bundle at a label `_promotion_is_blocked` permits AND carries the
    content that decision read, per
    `_promotion_carries_the_adjudicated_content`. Identified by column, because
    only one cell was ever validated; and no waiver is granted at all from a
    table that declares any `WAIVER_FIELDS` name twice, since which cell each
    part of the decision was read from is then not recoverable. The scan is
    over CELLS rather than named fields, because `csv.DictReader` hides an
    overwide row's extra cells and a duplicated header's shadowed column, and a
    blocking id written into either is a leak a field-keyed scan reports clean.

    Outside a parsable table -- a `.bnd`, a `.yaml`, a `.tsv` that will not parse
    or whose two readings disagree -- there is no row to read a citation from and
    no column in which a weaker label could be written, so the whole text is
    scanned and any blocking id in it is a leak.
    """
    found: list[str] = []
    rows = blocking_rows(root)
    decisions = adjudication_index(root)
    staged_basenames = _staged_basenames(root)
    identifiers = {next(iter(row)): row for row in rows}
    ids = {row[next(iter(row))].strip() for row in rows}
    # Blocking staged id -> the confidence label the STAGED row used. Needed by
    # the provenance detectors, which reach a blocking row by its id rather than
    # by its content, and so cannot read it off a matched edge pair.
    staged_confidences = {
        row[next(iter(row))].strip(): (row.get("confidence") or "").strip().lower()
        for row in rows
    }
    # The staged rows themselves, for the content correspondence a waiver needs.
    staged_by_id = {row[next(iter(row))].strip(): row for row in rows}
    # An edge carries the DECISION that blocked it and the confidence label the
    # staged row used, because what is blocked depends on both. See
    # `_promotion_is_blocked`.
    edges = {
        (row["source"].strip(), row["target"].strip()): (
            decisions.get(row[next(iter(row))].strip(), "UNRESOLVED"),
            (row.get("confidence") or "").strip().lower(),
        )
        for row in rows
        if "source" in row and "target" in row
    }
    rules = {
        (row["node_id"].strip(), _normalise(row["expression"]))
        for row in rows
        if "node_id" in row and "expression" in row
    }
    del identifiers

    for path in _scanned_files(root):
        relative = path.relative_to(root)
        text = path.read_text(encoding="utf-8", errors="ignore")

        table: list[dict[str, str]] | None = None
        header_cells: list[str] = []
        raw_cells: list[list[str]] = []
        if path.suffix == ".tsv":
            try:
                table = _rows(path)
                header_cells, raw_cells = _raw_rows(path)
            except (csv.Error, UnicodeDecodeError):  # pragma: no cover - defensive
                table = None
        # The two readers must describe the same rows, or a cell could be
        # exempted against the wrong row. If they ever disagree, no exemption is
        # granted and the whole text is scanned instead.
        cells_align = table is not None and len(raw_cells) == len(table)

        if table is None or not cells_align:
            # No rows to read a provenance citation from, and no `confidence`
            # column in which a permitted weaker form could be declared, so the
            # whole text is the surface and any blocking id in it is a leak.
            for staged_id in sorted(ids):
                if staged_id in text:
                    found.append(f"{relative}: carries blocking id {staged_id}")

        # Compiled logic: a rule variant reaching a .bnd loses its identifier, so
        # the rule itself is the only trace left. Compared as the node's COMPLETE
        # logic, never as a substring. A substring test is wrong here and was
        # measured to be wrong: the blocking variant for `E_ITGAVB3_5` is
        # `E_LIF or E_HBEGF`, which is a substring of the *unmodified* canonical
        # rule `E_LIF or E_HBEGF or E_SECRETORY_STATE` -- the very rule the
        # variant proposed to change. Substring matching reported all nine
        # committed models as leaking a row none of them carries.
        if path.suffix == ".bnd":
            compiled = _bnd_logic(text)
            for node_id, expression in compiled.items():
                if (node_id, expression) in rules:
                    found.append(
                        f"{relative}: node {node_id} is compiled with the blocking rule"
                    )
            # A blocked EDGE compiled into executable logic. The rule check above
            # cannot see this: it matches a staged rule variant's complete
            # expression, and a promoted edge appears as one TERM inside whatever
            # rule the target node ends up with. A `.bnd` also carries no
            # confidence column, so the adjudication's permitted weaker forms
            # (candidate/assumption) cannot be expressed here -- compiling an edge
            # asserts it as executable mechanism, which is strictly stronger than
            # the `verified` table label DRE009 rejects. Blocked unconditionally.
            for source, target in edges:
                logic = compiled.get(target)
                if logic is not None and source.lower() in _identifiers(logic):
                    found.append(
                        f"{relative}: node {target} is compiled with the blocking "
                        f"edge {source} -> {target}"
                    )

        if table is None:
            continue

        # A waiver is read from several cells, not just the citation, and
        # `csv.DictReader` silently keeps one column per repeated header name.
        # Where any of those fields is declared twice the cell a decision would
        # be read from is not recoverable, so no waiver is granted from this
        # table at all. See `WAIVER_FIELDS`.
        ambiguous = sorted(
            {name for name in WAIVER_FIELDS if header_cells.count(name) > 1}
        )

        # The header is outside every row, so a blocking id in it cannot be a
        # provenance citation and is never exempt.
        for cell in header_cells:
            for staged_id in sorted(ids):
                if staged_id in cell:
                    found.append(f"{relative}: carries blocking id {staged_id}")

        for index, row in enumerate(table):
            # Decided BEFORE the identifier and provenance-link checks below,
            # because what the adjudication permits this row to carry is what
            # decides whether carrying it is a leak.
            #
            # Promotion must CONSULT the adjudication, not merely avoid the four
            # ids that block today: a row declaring this bundle as its source
            # must name a staged row that was actually adjudicated, and that
            # decision -- read through `_promotion_is_blocked`, at THIS row's
            # confidence label -- must not block. An unadjudicated promotion is a
            # leak even though its id appears in no blocking list, which is the
            # case a detector keyed on blocking ids alone cannot see.
            source_table = (row.get("source_table") or "").strip()
            source_row = (row.get("source_row_id") or "").strip()
            promoted_confidence = (row.get("confidence") or "").strip().lower()
            permitted_citation = ""
            if names_this_bundle(source_table, staged_basenames):
                decision = decisions.get(source_row)
                if decision is None:
                    found.append(
                        f"{relative}: promotes {source_row or '<no source_row_id>'} "
                        f"from {source_table} with no adjudication decision"
                    )
                elif source_row in ids and ambiguous:
                    found.append(
                        f"{relative}: cites {source_row} from {source_table} in a "
                        f"table declaring {', '.join(ambiguous)} more than once, "
                        f"so which cell a waiver would be read from is not "
                        f"recoverable"
                    )
                elif source_row in ids:
                    blocked, why = _promotion_is_blocked(
                        decision=decision,
                        staged_confidence=staged_confidences.get(source_row, ""),
                        promoted_confidence=promoted_confidence,
                    )
                    if blocked:
                        found.append(
                            f"{relative}: promotes {source_row} from {source_table} "
                            f"whose adjudication blocks promotion ({decision}): {why}"
                        )
                    else:
                        # The label is permitted. Whether THIS row is what the
                        # decision permitted is a separate question, and the one
                        # a citation cannot answer about itself.
                        carries, mismatch = _promotion_carries_the_adjudicated_content(
                            promoted=row,
                            staged=staged_by_id[source_row],
                            source_table=source_table,
                        )
                        if carries:
                            permitted_citation = source_row
                        else:
                            found.append(
                                f"{relative}: cites {source_row} at a permitted "
                                f"label but does not carry the content that was "
                                f"adjudicated -- {mismatch}"
                            )

            # The identifier, scanned CELL by cell rather than field by field,
            # so a cell `csv.DictReader` drops -- an overwide row's extras, a
            # duplicated header's shadowed column -- cannot hide an id.
            #
            # Exactly one cell can be exempt, identified by COLUMN and not by
            # name and value: the single `source_row_id` column, carrying the
            # citation the adjudication permits this row to make. Keyed on name
            # and value instead, the exemption waived every cell that happened
            # to spell the permitted id, including ones nothing validated --
            # `_promotion_carries_the_adjudicated_content` was given exactly one
            # of them, the one `csv.DictReader` returned. If `source_row_id` is
            # not a unique column the authoritative cell is not identifiable, so
            # nothing is exempt: a table whose field mapping is ambiguous is not
            # one this gate can read a provenance claim out of. Everywhere else,
            # including this row's own notes, a blocking id is a copied row.
            # `permitted_citation` is set only where no waiver field is
            # declared twice, so this column exists and is unique.
            exempt = header_cells.index("source_row_id") if permitted_citation else -1
            for position, cell in enumerate(raw_cells[index]):
                if position == exempt and cell.strip() == permitted_citation:
                    continue
                for staged_id in sorted(ids):
                    if staged_id in cell:
                        found.append(f"{relative}: carries blocking id {staged_id}")

            if "source" in row and "target" in row:
                pair = (row["source"].strip(), row["target"].strip())
                if pair in edges:
                    edge_decision, staged_confidence = edges[pair]
                    blocked, why = _promotion_is_blocked(
                        decision=edge_decision,
                        staged_confidence=staged_confidence,
                        promoted_confidence=promoted_confidence,
                    )
                    if blocked:
                        found.append(
                            f"{relative}: carries the blocking edge "
                            f"{pair[0]} -> {pair[1]} at confidence="
                            f"{promoted_confidence or '<none>'} ({why})"
                        )
            if "node_id" in row and "expression" in row:
                rule = (row["node_id"].strip(), _normalise(row["expression"]))
                if rule in rules:
                    found.append(
                        f"{relative}: carries the blocking rule for {rule[0]} "
                        "(id may have been renamed)"
                    )
            # A preserved provenance link back into the bundle: promotion that
            # keeps its source row is caught even if the content was rewritten --
            # unless it is the `source_row_id` the adjudication permits this row
            # to declare, decided above. Scoped to that FIELD and not to the
            # value: `variant_id=DRE009` says the promoted row is NAMED after a
            # blocking staged row, which is a copied identifier and not a
            # citation, and a value-keyed skip waived it for spelling the same
            # thing the permitted citation spells.
            for field in ("source_row_id", "variant_id", "edge_id", "evidence_id"):
                value = (row.get(field) or "").strip()
                if not value or value not in ids:
                    continue
                if field == "source_row_id" and value == permitted_citation:
                    continue
                found.append(
                    f"{relative}: {field}={value} links to a blocking staged row"
                )
    return sorted(set(found))


def _plant(tmp: Path, relative: Path, text: str) -> Path:
    """A minimal tree: the real adjudication and bundle, plus one planted leak.

    Module level so every negative control shares one implementation. The
    adjudication is copied verbatim rather than synthesised, so the controls
    exercise the decisions actually recorded for this bundle.
    """
    staging = tmp / STAGING_RELATIVE
    if not staging.exists():
        staging.mkdir(parents=True)
        for path in (ROOT / STAGING_RELATIVE).iterdir():
            if path.is_file():
                (staging / path.name).write_bytes(path.read_bytes())
        adjudication = tmp / ADJUDICATION_RELATIVE
        adjudication.parent.mkdir(parents=True, exist_ok=True)
        adjudication.write_bytes((ROOT / ADJUDICATION_RELATIVE).read_bytes())
    planted = tmp / relative
    planted.parent.mkdir(parents=True, exist_ok=True)
    planted.write_text(text, encoding="utf-8")
    return planted


class StagedBundleIsVerbatim(unittest.TestCase):
    """The bundle is immutable, so its own manifest must keep verifying."""

    def test_every_manifest_entry_matches_its_recorded_digest(self) -> None:
        staging = ROOT / STAGING_RELATIVE
        entries = _rows(staging / "manifest.tsv")
        self.assertTrue(entries, "manifest.tsv is empty")
        for entry in entries:
            path = staging / entry["file"]
            with self.subTest(file=entry["file"]):
                self.assertTrue(path.is_file(), f"{entry['file']} is missing")
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    entry["sha256"].strip(),
                    f"{entry['file']} no longer matches the delivered bundle; a "
                    "staged file was edited in place, which destroys the record "
                    "of what the external reviewer sent",
                )

    def test_the_staging_directory_holds_exactly_its_manifest(self) -> None:
        """No quiet additions: an unlisted file is outside the integrity record."""
        staging = ROOT / STAGING_RELATIVE
        listed = {row["file"] for row in _rows(staging / "manifest.tsv")}
        listed.add("manifest.tsv")
        present = {path.name for path in staging.iterdir() if path.is_file()}
        self.assertEqual(present, listed)


class BlockingRowsCannotReachCanonicalOrExecutableArtifacts(unittest.TestCase):
    """The invariant the whole staging decision rests on."""

    def test_there_is_something_to_enforce(self) -> None:
        """Guard against the check silently becoming vacuous."""
        rows = blocking_rows(ROOT)
        self.assertTrue(
            rows,
            "no adjudicated row blocks promotion, so this module asserts "
            "nothing; if the bundle was cleared that must be a recorded decision",
        )
        # Every blocking decision must join to real staged content, or the
        # content checks below would silently have nothing to compare.
        decisions = [
            row
            for row in _rows(ROOT / ADJUDICATION_RELATIVE)
            if row["blocks_promotion"].strip().lower() == "yes"
        ]
        self.assertEqual(len(rows), len(decisions))
        self.assertTrue(
            any("source" in row and "target" in row for row in rows),
            "no blocking edge row, so the edge-content detector is untested",
        )
        self.assertTrue(
            any("node_id" in row and "expression" in row for row in rows),
            "no blocking rule row, so the rule-content detector is untested",
        )

    def test_no_blocking_row_reaches_a_canonical_or_executable_artifact(self) -> None:
        self.assertEqual(
            leaks(ROOT),
            [],
            "adjudicated blocks_promotion=yes rows have reached canonical or "
            "executable artifacts; overturn the adjudication before promoting",
        )


class TheGateIsKnownToFail(unittest.TestCase):
    """Negative controls. A detector nobody has watched fire is not a gate.

    Each control plants one realistic promotion mistake into a copy of the
    quarantine record and asserts `leaks` reports it, so the three detectors are
    demonstrated independently rather than assumed.
    """

    def _planted(self, tmp: Path, relative: Path, text: str) -> Path:
        return _plant(tmp, relative, text)

    def test_a_renamed_blocking_edge_is_still_caught(self) -> None:
        """The exact case the identifier-only check missed."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._planted(
                tmp,
                Path("models") / "superset" / "vNext" / "edge_evidence.tsv",
                "edge_id\tsource\ttarget\tsign\tevidence_id\tconfidence\t"
                "variant_id\tnotes\n"
                "LIT-IL11-999\tX_IL11\tE_ITGA2B1\tactivation\tLIT-NEW-001\t"
                "verified\tpromoted\trenamed on promotion\n",
            )
            reported = leaks(tmp)
            self.assertTrue(
                any("blocking edge X_IL11 -> E_ITGA2B1" in line for line in reported),
                f"a renamed blocking edge was not caught: {reported}",
            )

    def test_a_compiled_blocking_rule_is_still_caught(self) -> None:
        """Compiling into a .bnd drops the identifier entirely."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            expression = next(
                row["expression"]
                for row in blocking_rows(ROOT)
                if row.get("node_id") == "E_ITGAVB3_5"
            )
            self._planted(
                tmp,
                Path("models") / "superset" / "vNext" / "network.bnd",
                "Node E_ITGAVB3_5 {\n"
                f"  logic = ({expression});\n"
                "  rate_up = @logic ? 1.0 : 0.0;\n"
                "}\n",
            )
            reported = leaks(tmp)
            self.assertTrue(
                any(
                    "node E_ITGAVB3_5 is compiled with the blocking rule" in line
                    for line in reported
                ),
                f"a compiled blocking rule was not caught: {reported}",
            )

    def test_a_rewritten_row_that_keeps_its_provenance_link_is_caught(self) -> None:
        """Content changed, but the source row is still declared."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._planted(
                tmp,
                Path("models") / "superset" / "vNext" / "rule_variants.tsv",
                "variant_id\tnode_id\texpression\tstatus\tdefault_in_family\t"
                "source_table\tsource_row_id\tevidence_ids\tnotes\n"
                "promoted_lif_v2\tE_RECEPTIVE_SURFACE\tE_SOX17\tactive\ttrue\t"
                "promoted\tdr20260911_lif_soft_surface\tDR-ARCH-LIF-001\t"
                "rewritten but same source row\n",
            )
            reported = leaks(tmp)
            self.assertTrue(
                any("links to a blocking staged row" in line for line in reported),
                f"a preserved provenance link was not caught: {reported}",
            )

    def test_an_unadjudicated_promotion_from_this_bundle_is_caught(self) -> None:
        """The promotion path must consult the adjudication, not dodge four ids.

        This row names no blocking id, carries no blocking content and keeps a
        clean provenance link -- every other detector passes it. It is still a
        leak, because it promotes a staged row that was never adjudicated.
        """
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._planted(
                tmp,
                Path("models") / "superset" / "vNext" / "rule_variants.tsv",
                "variant_id\tnode_id\texpression\tstatus\tdefault_in_family\t"
                "source_table\tsource_row_id\tevidence_ids\tnotes\n"
                "promoted_never_reviewed\tE_PAEP\tS_PGR\tactive\ttrue\t"
                "rule_variants.tsv\tdr20260911_not_adjudicated\tDR-X-001\t"
                "promoted without any adjudication decision\n",
            )
            reported = leaks(tmp)
            self.assertTrue(
                any("no adjudication decision" in line for line in reported),
                f"an unadjudicated promotion was not caught: {reported}",
            )

    def test_a_blocking_row_promoted_with_honest_provenance_is_caught(self) -> None:
        """Declaring the blocking source row honestly does not make it promotable.

        At the REJECTED label, which is the whole of DRE009's condition. An
        earlier revision planted this row at `candidate` and asserted it was
        refused -- but that refusal came from a blanket `source_row in
        blocking_ids` rule rather than from the record, and the record permits
        DRE009 at `candidate`. Planted at `verified` so the control demonstrates
        the detector it is named for instead of the paraphrase that stood in for
        it; the permitted labels are asserted in
        `TheGateEnforcesTheAdjudicationNotAParaphrase`.
        """
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._planted(
                tmp,
                Path("models") / "superset" / "vNext" / "edge_evidence.tsv",
                "edge_id\tsource\ttarget\tsign\tevidence_id\tconfidence\t"
                "variant_id\tsource_table\tsource_row_id\tnotes\n"
                "LIT-NEW-001\tX_IL11\tE_SOX17\tactivation\tLIT-NEW-001\t"
                "verified\tpromoted\tedge_evidence.tsv\tDRE009\t"
                "different biology, but promoted from a blocking row\n",
            )
            reported = leaks(tmp)
            self.assertTrue(
                any("blocks promotion" in line for line in reported),
                f"a blocking-sourced promotion was not caught: {reported}",
            )

    def test_a_repository_relative_staging_path_is_recognised(self) -> None:
        """The spelling the repository actually uses for `source_table`.

        `complete_nodes.tsv` cites `context/literature/candidate-nodes.tsv`, so a
        repository-relative path is the likely spelling for a real promotion. An
        exact-basename test accepted this row silently.
        """
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._planted(
                tmp,
                Path("models") / "superset" / "vNext" / "rule_variants.tsv",
                "variant_id\tnode_id\texpression\tstatus\tdefault_in_family\t"
                "source_table\tsource_row_id\tevidence_ids\tnotes\n"
                "promoted_via_full_path\tE_PAEP\tS_PGR\tactive\ttrue\t"
                f"{STAGING_RELATIVE.as_posix()}/rule_variants.tsv\t"
                "dr20260911_not_adjudicated\tDR-X-001\tpromoted via full path\n",
            )
            reported = leaks(tmp)
            self.assertTrue(
                any("no adjudication decision" in line for line in reported),
                f"a repository-relative staging path was not recognised: {reported}",
            )

    def test_every_plausible_spelling_of_the_bundle_is_recognised(self) -> None:
        """The matcher itself, at the boundary, rather than only through a tree."""
        basenames = _staged_basenames(ROOT)
        self.assertIn("rule_variants.tsv", basenames)
        for spelling in (
            BUNDLE,
            f"{STAGING_RELATIVE.as_posix()}/rule_variants.tsv",
            f"./{STAGING_RELATIVE.as_posix()}/edge_evidence.tsv",
            f"/abs/checkout/{STAGING_RELATIVE.as_posix()}/mechanisms.tsv",
            STAGING_RELATIVE.as_posix().replace("/", "\\") + "\\references.tsv",
            "rule_variants.tsv",
        ):
            with self.subTest(spelling=spelling):
                self.assertTrue(names_this_bundle(spelling, basenames))
        for spelling in (
            "",
            "context/literature/candidate-nodes.tsv",
            "models/extended/adoc-literature-v0.2.0/node_dictionary.tsv",
            "context/literature/staging/some_other_bundle/rule_variants.tsv",
        ):
            with self.subTest(spelling=spelling):
                self.assertFalse(names_this_bundle(spelling, basenames))

    def test_a_clean_tree_reports_nothing(self) -> None:
        """The controls above must fail for their planted reason, not always."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._planted(
                tmp,
                Path("models") / "superset" / "vNext" / "edge_evidence.tsv",
                "edge_id\tsource\ttarget\tsign\tevidence_id\tconfidence\t"
                "variant_id\tnotes\n"
                "LIT-OK-001\tS_PGR\tE_PAEP\tactivation\tLIT-OK-001\tverified\t"
                "base\tunrelated\n",
            )
            self.assertEqual(leaks(tmp), [])

    def test_a_blocked_edge_compiled_into_executable_logic_is_caught(self) -> None:
        """DRE009's edge as a TERM inside a compiled rule -- the B15 counterexample.

        The rule detector cannot see this. It matches a staged rule variant's
        COMPLETE expression, whereas a promoted edge appears as one term inside
        whatever rule the target node ends up with, alongside terms that have
        nothing to do with the bundle. Without the edge-in-`.bnd` check this tree
        passes every other detector while shipping rejected biology as
        executable model logic.
        """
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._planted(
                tmp,
                Path("models") / "superset" / "vNext" / "network.bnd",
                "Node E_ITGA2B1 {\n"
                "  logic = E_GP130_STAT3 and (X_IL11 or E_SOX17);\n"
                "  rate_up = @logic ? 1.0 : 0.0;\n"
                "}\n",
            )
            reported = leaks(tmp)
            self.assertTrue(
                any(
                    "compiled with the blocking edge X_IL11 -> E_ITGA2B1" in line
                    for line in reported
                ),
                f"a compiled blocking edge was not caught: {reported}",
            )

    def test_a_cell_dictreader_drops_cannot_hide_a_blocking_id(self) -> None:
        """Two malformed tables that a field-keyed scan reads as clean.

        `csv.DictReader` puts a row's extra cells in a list under the key
        `None`, and keeps only the last of two identically named columns. A scan
        iterating `row[field]` therefore never sees an id written into either --
        while anyone opening the file does. Neither shape is exotic: a stray tab
        produces the first, a copy-pasted header the second.
        """
        planted = {
            "overwide row": (
                "edge_id\tsource\ttarget\tsign\tevidence_id\tconfidence\t"
                "variant_id\tnotes\n"
                "LIT-OK-001\tS_PGR\tE_PAEP\tactivation\tLIT-OK-001\t"
                "verified\tbase\tordinary\tDRE009\n"
            ),
            "duplicate header": (
                "edge_id\tsource\ttarget\tsign\tevidence_id\tconfidence\t"
                "variant_id\tnotes\tnotes\n"
                "LIT-OK-001\tS_PGR\tE_PAEP\tactivation\tLIT-OK-001\t"
                "verified\tbase\tDRE009\tordinary\n"
            ),
        }
        for shape, table in planted.items():
            with self.subTest(shape=shape):
                with tempfile.TemporaryDirectory() as raw:
                    tmp = Path(raw)
                    self._planted(
                        tmp,
                        Path("models") / "superset" / "vNext" / "edge_evidence.tsv",
                        table,
                    )
                    reported = leaks(tmp)
                self.assertTrue(
                    any("carries blocking id DRE009" in line for line in reported),
                    f"a blocking id in a cell DictReader drops was not caught: "
                    f"{reported}",
                )

    def test_a_short_node_name_does_not_match_a_longer_one(self) -> None:
        """The edge check is term-level, not substring.

        `X_IL11` must not be found merely because some other identifier contains
        those characters, or the gate would fire on unrelated models the way the
        substring rule check once did.
        """
        self.assertIn("x_il11", _identifiers("E_GP130 and (X_IL11 or E_SOX17)"))
        self.assertNotIn("x_il11", _identifiers("E_X_IL11_RELAY or E_SOX17"))


class TheGateEnforcesTheAdjudicationNotAParaphrase(unittest.TestCase):
    """DRE009 rejects a confidence LABEL, and the gate must say only that.

    Its recorded basis objects to marking an integrin-alpha2 expression/protein
    observation as a `verified` receptor-activity edge, and it leaves the edge
    admissible once downgraded or once the target node is redefined as an
    abundance state. A blanket ban on the edge pair -- which an earlier revision
    of this module used -- is stronger than the record and would refuse a
    promotion the adjudication permits. Both directions are asserted here so the
    gate cannot drift to either.
    """

    def _promoted_edge(
        self, tmp: Path, confidence: str, *, provenance: bool
    ) -> list[str]:
        """Plant one promotion of DRE009's edge, with or without its provenance.

        Both shapes matter and only the first used to be tested. Without the
        provenance columns the row is a renamed copy, which no provenance
        detector can see. With them it is what an honest promotion actually
        writes -- and that is the shape three separate `id in blocking_ids`
        rules refused at every label, including the labels the adjudication
        permits.
        """
        columns = "edge_id\tsource\ttarget\tsign\tevidence_id\tconfidence\tvariant_id"
        values = (
            f"LIT-IL11-010\tX_IL11\tE_ITGA2B1\tactivation\tLIT-NEW-001\t"
            f"{confidence}\tpromoted"
        )
        if provenance:
            columns += "\tsource_table\tsource_row_id"
            values += "\tedge_evidence.tsv\tDRE009"
        _plant(
            tmp,
            Path("models") / "superset" / "vNext" / "edge_evidence.tsv",
            f"{columns}\tnotes\n{values}\tre-adjudicated promotion\n",
        )
        return leaks(tmp)

    def test_promotion_at_the_rejected_confidence_is_refused(self) -> None:
        for provenance in (False, True):
            with self.subTest(provenance=provenance):
                with tempfile.TemporaryDirectory() as raw:
                    reported = self._promoted_edge(
                        Path(raw), "verified", provenance=provenance
                    )
                self.assertTrue(
                    any(
                        "blocking edge X_IL11 -> E_ITGA2B1" in line for line in reported
                    ),
                    f"a `verified` promotion of the rejected edge was allowed: "
                    f"{reported}",
                )

    def test_promotion_downgraded_to_candidate_is_permitted(self) -> None:
        """The case the blanket ban wrongly refused, in both promotion shapes.

        Asserted as NOTHING reported, rather than as no reported line mentioning
        the edge. The blanket identifier and provenance rules refuse the honest
        row without ever naming the edge, so an edge-scoped filter reads green
        while the gate is in fact refusing the promotion -- which is exactly how
        this defect survived the round that introduced the permitted forms.
        """
        for provenance in (False, True):
            with self.subTest(provenance=provenance):
                with tempfile.TemporaryDirectory() as raw:
                    reported = self._promoted_edge(
                        Path(raw), "candidate", provenance=provenance
                    )
                self.assertEqual(
                    reported,
                    [],
                    "the adjudication permits this edge as candidate, but the "
                    "gate refused it -- the gate is enforcing a paraphrase, not "
                    "the record",
                )

    def test_promotion_downgraded_to_assumption_is_permitted(self) -> None:
        for provenance in (False, True):
            with self.subTest(provenance=provenance):
                with tempfile.TemporaryDirectory() as raw:
                    reported = self._promoted_edge(
                        Path(raw), "assumption", provenance=provenance
                    )
                self.assertEqual(reported, [])

    def test_declaring_provenance_does_not_change_the_verdict(self) -> None:
        """The defect itself, stated as the difference the columns make.

        The same edge at the same label, promoted twice: once as a bare renamed
        row, once declaring `source_table`/`source_row_id`. The gate must reach
        the same verdict on both, because provenance records where a row came
        from and is not itself a promotion. It did not: the policy function
        permitted the downgrade while the identifier scan, the provenance-link
        check and the adjudication check each refused the row for naming DRE009
        at all, so the only promotion the gate accepted was one that concealed
        its source.
        """
        for confidence in ("verified", "candidate", "assumption"):
            with self.subTest(confidence=confidence):
                with tempfile.TemporaryDirectory() as raw:
                    bare = self._promoted_edge(Path(raw), confidence, provenance=False)
                with tempfile.TemporaryDirectory() as raw:
                    honest = self._promoted_edge(Path(raw), confidence, provenance=True)
                # The VERDICT, not the lines. A blocked honest row rightly draws
                # extra provenance-specific reports the bare row cannot draw, so
                # comparing line lists would either be vacuous or would have to
                # filter out the id -- and filtering out the id is what hides
                # this defect, because every blanket rule reports under it.
                self.assertEqual(
                    bool(honest),
                    bool(bare),
                    f"declaring where this promotion came from changed the "
                    f"verdict at confidence={confidence!r}, which teaches "
                    f"promotions to hide their provenance. "
                    f"bare={bare} honest={honest}",
                )

    def test_a_label_the_record_does_not_name_is_not_admissible(self) -> None:
        """`hypothesis` reads as weaker than `candidate`, and is not permitted.

        DRE009's note says "Admissible only as candidate/assumption". A gate
        that also admits `hypothesis` is ranking confidence labels the
        adjudicator never enumerated and calling the result the decision --
        which is the substitution this whole module is named against, made by
        the gate rather than by a promoter. Both promotion shapes, because the
        label decides them both.
        """
        for provenance in (False, True):
            with self.subTest(provenance=provenance):
                with tempfile.TemporaryDirectory() as raw:
                    reported = self._promoted_edge(
                        Path(raw), "hypothesis", provenance=provenance
                    )
                self.assertTrue(
                    any(
                        "blocking edge X_IL11 -> E_ITGA2B1" in line for line in reported
                    ),
                    f"a label the record does not name was admitted: {reported}",
                )

    def test_an_executable_promotion_is_blocked_at_every_label(self) -> None:
        """A `.bnd` has no weak-confidence representation, so nothing is permitted.

        The forms the adjudication permits are a CONFIDENCE LABEL on a table
        row. Compiling the edge into executable logic asserts it as mechanism,
        which is strictly stronger than the `verified` table label DRE009
        rejects, and a `.bnd` carries no column a downgrade could be written in.
        Saying `candidate` in a comment must not stand in for one.
        """
        for comment in ("", "  // promoted as candidate from DRE009\n"):
            with self.subTest(comment=bool(comment)):
                with tempfile.TemporaryDirectory() as raw:
                    _plant(
                        Path(raw),
                        Path("models") / "superset" / "vNext" / "network.bnd",
                        "Node E_ITGA2B1 {\n"
                        f"{comment}"
                        "  logic = E_GP130_STAT3 and (X_IL11 or E_SOX17);\n"
                        "  rate_up = @logic ? 1.0 : 0.0;\n"
                        "}\n",
                    )
                    reported = leaks(Path(raw))
                self.assertTrue(
                    any(
                        "compiled with the blocking edge X_IL11 -> E_ITGA2B1" in line
                        for line in reported
                    ),
                    f"an executable promotion was permitted: {reported}",
                )

    def test_a_decision_with_no_weaker_form_blocks_through_the_provenance_path(
        self,
    ) -> None:
        """The hole delegating could have opened, closed by control.

        Making the provenance detectors consult the adjudication is only safe
        while a decision that admits no promotable form still blocks there.
        `UNRESOLVED` and `REJECT_PROVENANCE` admit none, so a row citing one is
        refused whatever label it claims -- including the labels DRE009 permits.
        Run through a planted tree rather than on the policy function alone,
        because what B17 broke was the wiring and not the policy.
        """
        for staged_id in (
            "dr20260911_lif_soft_surface",
            "dr20260911_itgav_no_secretory_absorption",
        ):
            for confidence in ("candidate", "assumption"):
                with self.subTest(staged_id=staged_id, confidence=confidence):
                    with tempfile.TemporaryDirectory() as raw:
                        _plant(
                            Path(raw),
                            Path("models") / "superset" / "vNext" / "rule_variants.tsv",
                            "variant_id\tnode_id\texpression\tconfidence\t"
                            "source_table\tsource_row_id\tnotes\n"
                            f"promoted_weak\tE_PAEP\tS_PGR\t{confidence}\t"
                            f"rule_variants.tsv\t{staged_id}\tdowngraded\n",
                        )
                        reported = leaks(Path(raw))
                    self.assertTrue(
                        any("admits no promoted form" in line for line in reported),
                        f"a decision with no promotable form was permitted "
                        f"through the provenance path: {reported}",
                    )

    def test_a_decision_admitting_no_weaker_form_still_blocks_outright(self) -> None:
        """REJECT_PROVENANCE and UNRESOLVED have no promotable form.

        Asserted on the policy function directly, because the staged blocking
        rows carrying those decisions are rule variants rather than edges.
        """
        for decision in ("REJECT_PROVENANCE", "UNRESOLVED"):
            for confidence in ("candidate", "assumption", "verified", ""):
                with self.subTest(decision=decision, confidence=confidence):
                    blocked, _ = _promotion_is_blocked(
                        decision=decision,
                        staged_confidence="verified",
                        promoted_confidence=confidence,
                    )
                    self.assertTrue(blocked)

    def test_an_unknown_decision_blocks_rather_than_silently_permitting(self) -> None:
        blocked, why = _promotion_is_blocked(
            decision="SOME_FUTURE_DECISION",
            staged_confidence="verified",
            promoted_confidence="candidate",
        )
        self.assertTrue(blocked)
        self.assertIn("unrecognised", why)


class AWaiverCoversOnlyWhatWasAdjudicated(unittest.TestCase):
    """A citation is a claim about a staged row, and the gate must check it.

    DRE009 is adjudicated `REJECT_CONFIDENCE_LABEL`, which permits promoting ONE
    edge -- `X_IL11 -> E_ITGA2B1`, activating -- at a weaker label. Reading that
    permission off the citation id and the promoted label alone, without looking
    at what the row says, turns `source_row_id=DRE009` into a way to move
    unreviewed biology into a canonical table under provenance that is false
    about the only thing provenance records. These controls plant exactly that,
    because a gate accepting a citation it never checked is worse than one with
    no provenance detector at all: the row then arrives looking audited.
    """

    def _cited(self, tmp: Path, row: str) -> list[str]:
        _plant(
            tmp,
            Path("models") / "superset" / "vNext" / "edge_evidence.tsv",
            "edge_id\tsource\ttarget\tsign\tevidence_id\tconfidence\t"
            "variant_id\tsource_table\tsource_row_id\tnotes\n" + row,
        )
        return leaks(tmp)

    def test_unrelated_biology_cannot_be_promoted_under_this_citation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            reported = self._cited(
                Path(raw),
                "LIT-FAKE-001\tX_FAKE\tE_FAKE\tactivation\tLIT-FAKE-001\t"
                "candidate\tpromoted\tedge_evidence.tsv\tDRE009\t"
                "biology no adjudicator ever read\n",
            )
        self.assertTrue(
            any(
                "does not carry the content that was adjudicated" in line
                for line in reported
            ),
            f"unreviewed biology was promoted under a DRE009 citation: {reported}",
        )

    def test_the_same_edge_with_its_sign_reversed_is_not_the_same_edge(self) -> None:
        """The case a source/target-only comparison would miss.

        Both nodes match the staged row; the direction of effect does not.
        Reversing a sign changes the mechanism, and what was read was
        `activation`.
        """
        with tempfile.TemporaryDirectory() as raw:
            reported = self._cited(
                Path(raw),
                "LIT-IL11-011\tX_IL11\tE_ITGA2B1\tinhibition\tLIT-NEW-001\t"
                "candidate\tpromoted\tedge_evidence.tsv\tDRE009\t"
                "sign reversed on promotion\n",
            )
        self.assertTrue(
            any("sign=inhibition" in line for line in reported),
            f"a sign-reversed promotion kept the waiver: {reported}",
        )

    def test_the_citation_must_name_the_file_the_decision_was_recorded_against(
        self,
    ) -> None:
        """`source_table` is half the citation, and was not checked either.

        DRE009 is adjudicated in `edge_evidence.tsv`. A row citing the bundle's
        `rule_variants.tsv` for it describes a row that does not exist, so no
        waiver can be read off it.
        """
        with tempfile.TemporaryDirectory() as raw:
            reported = self._cited(
                Path(raw),
                "LIT-IL11-012\tX_IL11\tE_ITGA2B1\tactivation\tLIT-NEW-001\t"
                "candidate\tpromoted\trule_variants.tsv\tDRE009\t"
                "right row, wrong staged file\n",
            )
        self.assertTrue(
            any("does not name edge_evidence.tsv" in line for line in reported),
            f"a citation naming the wrong staged file kept the waiver: {reported}",
        )

    def test_an_ambiguous_waiver_column_grants_no_exemption(self) -> None:
        """A waiver is read from several cells, and any of them can be shadowed.

        `csv.DictReader` keeps one column per repeated header name and discards
        the rest, so a table declaring a waiver field twice presents one value to
        the gate and another to a reader. Only `source_row_id` uniqueness was
        checked, which left the LABEL and the BIOLOGY shadowable: a row reading
        `verified` first and `candidate` second was waived on the second, and one
        reading `X_FAKE` first and `X_IL11` second passed the content check on
        the second while carrying the first.

        The duplicated cells here AGREE with what the gate read in the
        `source_row_id` case and disagree in the others, because both shapes have
        to be refused. No waiver is granted from such a table at all: which cell
        each part of the decision came from is not recoverable, and a waiver is a
        claim about a specific row.
        """
        planted = {
            "source_row_id": (
                "edge_id\tsource\ttarget\tsign\tevidence_id\tconfidence\t"
                "variant_id\tsource_table\tsource_row_id\tsource_row_id\tnotes\n"
                "LIT-IL11-010\tX_IL11\tE_ITGA2B1\tactivation\tLIT-NEW-001\t"
                "candidate\tpromoted\tedge_evidence.tsv\tDRE009\tDRE009\t"
                "provenance declared twice\n"
            ),
            "confidence": (
                "edge_id\tsource\ttarget\tsign\tevidence_id\tconfidence\t"
                "confidence\tvariant_id\tsource_table\tsource_row_id\tnotes\n"
                "LIT-IL11-010\tX_IL11\tE_ITGA2B1\tactivation\tLIT-NEW-001\t"
                "verified\tcandidate\tpromoted\tedge_evidence.tsv\tDRE009\t"
                "rejected label shadowed by a permitted one\n"
            ),
            "source": (
                "edge_id\tsource\tsource\ttarget\tsign\tevidence_id\t"
                "confidence\tvariant_id\tsource_table\tsource_row_id\tnotes\n"
                "LIT-IL11-010\tX_FAKE\tX_IL11\tE_ITGA2B1\tactivation\t"
                "LIT-NEW-001\tcandidate\tpromoted\tedge_evidence.tsv\tDRE009\t"
                "unreviewed biology shadowed by the adjudicated edge\n"
            ),
        }
        for field, table in planted.items():
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as raw:
                    _plant(
                        Path(raw),
                        Path("models") / "superset" / "vNext" / "edge_evidence.tsv",
                        table,
                    )
                    reported = leaks(Path(raw))
                self.assertTrue(
                    any(
                        f"declaring {field} more than once" in line for line in reported
                    ),
                    f"a shadowed {field} column was treated as authoritative: "
                    f"{reported}",
                )
                self.assertTrue(
                    any("carries blocking id DRE009" in line for line in reported),
                    f"the exemption survived an ambiguous header: {reported}",
                )

    def test_only_the_provenance_cell_may_name_the_staged_row(self) -> None:
        """A waiver covers the citation, not every mention of the id.

        Both rows below are promotions the adjudication permits -- right edge,
        right sign, right label, honest `source_row_id`. Each additionally
        carries the staged id somewhere the waiver does not reach: as the
        promoted row's OWN identifier, and in its prose. Neither is a citation.
        An exemption keyed on the value rather than the column waived them for
        spelling what the citation spells, which is the same defect the
        duplicate-column controls pin, in the two detectors that read a row
        after the waiver is granted.
        """
        planted = {
            "variant_id is the staged id": (
                "LIT-IL11-010\tX_IL11\tE_ITGA2B1\tactivation\tLIT-NEW-001\t"
                "candidate\tDRE009\tedge_evidence.tsv\tDRE009\t"
                "promoted row named after the staged row\n"
            ),
            "notes repeat the staged id": (
                "LIT-IL11-010\tX_IL11\tE_ITGA2B1\tactivation\tLIT-NEW-001\t"
                "candidate\tpromoted\tedge_evidence.tsv\tDRE009\t"
                "copied verbatim from DRE009\n"
            ),
        }
        for shape, row in planted.items():
            with self.subTest(shape=shape):
                with tempfile.TemporaryDirectory() as raw:
                    reported = self._cited(Path(raw), row)
                self.assertTrue(
                    any("carries blocking id DRE009" in line for line in reported),
                    f"a blocking id outside the provenance cell was waived: {reported}",
                )
        with tempfile.TemporaryDirectory() as raw:
            reported = self._cited(
                Path(raw),
                "LIT-IL11-010\tX_IL11\tE_ITGA2B1\tactivation\tLIT-NEW-001\t"
                "candidate\tDRE009\tedge_evidence.tsv\tDRE009\t"
                "promoted row named after the staged row\n",
            )
        self.assertTrue(
            any("variant_id=DRE009" in line for line in reported),
            f"the provenance-link detector waived a copied identifier: {reported}",
        )

    def test_the_promotion_the_adjudication_permits_still_passes(self) -> None:
        """The controls above must refuse false citations, not every citation."""
        with tempfile.TemporaryDirectory() as raw:
            reported = self._cited(
                Path(raw),
                "LIT-IL11-010\tX_IL11\tE_ITGA2B1\tactivation\tLIT-NEW-001\t"
                "candidate\tpromoted\tedge_evidence.tsv\tDRE009\t"
                "downgraded exactly as the adjudication permits\n",
            )
        self.assertEqual(reported, [])


class TheRedefinitionRouteIsNotAPromotionRoute(unittest.TestCase):
    """The gate and the adjudication must agree about the abundance-state route.

    DRE009's note once read as offering two ways past the quarantine: downgrade
    to candidate/assumption, OR promote at `verified` once `E_ITGA2B1` is
    redefined from a receptor-activity/heterodimer state to an abundance state.
    The gate has always honoured the first and refused to infer the second,
    because redefining the target changes the biological claim that was
    adjudicated, and a gate that inferred it would let an unreviewed semantic
    change enter a canonical table under provenance that says it was reviewed.

    An independent reviewer read that gap the other way -- the gate enforcing a
    stronger prohibition than the record wrote -- and it was a fair reading of
    two artifacts that disagreed. The disagreement is closed by making the record
    say what the gate does, not by teaching the gate to infer redefinitions. This
    pins both halves so they cannot drift apart again.

    What is NOT asserted here: that the redefined biology is wrong. It has not
    been adjudicated, and this class does not adjudicate it.
    """

    def _dre009_note(self) -> str:
        for row in _rows(ROOT / ADJUDICATION_RELATIVE):
            if row["staged_id"].strip() == "DRE009":
                return row["note"]
        self.fail("DRE009 is no longer in the adjudication record")

    def test_unchanged_content_passes_only_at_candidate_or_assumption(self) -> None:
        """The permission the record does grant, enforced at its exact edge."""
        for label in sorted(ADMISSIBLE_WEAKER_LABELS):
            with self.subTest(promoted=label):
                blocked, why = _promotion_is_blocked(
                    decision="REJECT_CONFIDENCE_LABEL",
                    staged_confidence="verified",
                    promoted_confidence=label,
                )
                self.assertFalse(blocked, f"{label!r} is admitted by the record: {why}")

        for label in ("verified", "high", "established"):
            with self.subTest(promoted=label):
                blocked, _ = _promotion_is_blocked(
                    decision="REJECT_CONFIDENCE_LABEL",
                    staged_confidence="verified",
                    promoted_confidence=label,
                )
                self.assertTrue(
                    blocked,
                    f"{label!r} is not a weaker label the record names, so the "
                    "quarantine must hold",
                )

    def test_the_record_does_not_advertise_the_redefinition_as_a_route(self) -> None:
        """The record must not appear to authorise what the gate refuses.

        Deliberately a semantic check and not a string ban: the note still
        DISCUSSES the redefinition, because deleting that history would erase why
        the edge was rejected. What it must no longer do is present it as a way
        to promote under this row, so the note has to carry the refusal.
        """
        note = self._dre009_note().lower()
        self.assertIn(
            "abundance",
            note,
            "the basis for rejecting the edge must stay in the record",
        )
        self.assertTrue(
            "requires a new adjudication" in note or "new adjudication" in note,
            "the note discusses the abundance-state redefinition without saying "
            f"it needs a fresh decision, so it still reads as a route: {note!r}",
        )

    def test_a_redefined_target_is_not_the_adjudicated_content(self) -> None:
        """A transformed row is a different claim, whatever it cites.

        The abundance-state redefinition is exactly the transformation the gate
        must not wave through, so it is checked the way any other substitution
        is: the promoted row no longer carries the staged row's content, and the
        waiver does not reach it.
        """
        staged = {
            "source": "X_IL11",
            "target": "E_ITGA2B1",
            "sign": "activating",
            "confidence": "verified",
            "_staged_file": "edge_evidence.tsv",
        }
        transformed = dict(staged, target="E_ITGA2_ABUNDANCE")
        carries, why = _promotion_carries_the_adjudicated_content(
            promoted=transformed,
            staged=staged,
            source_table="edge_evidence.tsv",
        )
        self.assertFalse(
            carries,
            "a promotion that retargets the edge onto a redefined node was "
            f"treated as the adjudicated content: {why}",
        )

    def test_the_unchanged_row_still_does_carry_it(self) -> None:
        """The companion direction, so the check above is not vacuously strict."""
        staged = {
            "source": "X_IL11",
            "target": "E_ITGA2B1",
            "sign": "activating",
            "confidence": "verified",
            "_staged_file": "edge_evidence.tsv",
        }
        carries, why = _promotion_carries_the_adjudicated_content(
            promoted=dict(staged, confidence="candidate"),
            staged=staged,
            source_table="edge_evidence.tsv",
        )
        self.assertTrue(carries, f"the unchanged edge lost its waiver: {why}")


class TheAdmissibleLabelsComeFromTheRecord(unittest.TestCase):
    """`ADMISSIBLE_WEAKER_LABELS` is a reading of the adjudication, so check it.

    A hard-coded set is only as good as its correspondence to the file it claims
    to transcribe, and that correspondence is exactly what drifts. This pins it
    both ways against every `REJECT_CONFIDENCE_LABEL` note in the record: each
    admitted label must be named there, and a small vocabulary of labels this
    module does NOT admit must be absent.

    The second half pins a vocabulary and not the class of all possible labels;
    a record naming something outside that list would pass here. It is a guard
    against this specific drift recurring, not a proof that the set is complete.
    """

    def _notes(self) -> list[str]:
        return [
            row["note"]
            for row in _rows(ROOT / ADJUDICATION_RELATIVE)
            if row["decision"].strip().upper() == "REJECT_CONFIDENCE_LABEL"
        ]

    def test_there_is_a_recorded_permission_to_check(self) -> None:
        self.assertTrue(
            self._notes(),
            "no REJECT_CONFIDENCE_LABEL row remains, so the permitted labels "
            "assert nothing and must be re-derived from whatever replaced it",
        )

    def test_every_admitted_label_is_named_by_the_record(self) -> None:
        for note in self._notes():
            for label in sorted(ADMISSIBLE_WEAKER_LABELS):
                with self.subTest(label=label):
                    self.assertIn(
                        label,
                        note.lower(),
                        f"this module admits {label!r}, which the adjudication "
                        f"note does not name: {note!r}",
                    )

    def test_a_label_the_record_omits_is_not_admitted(self) -> None:
        """The drift that happened, pinned so it cannot happen again silently."""
        for note in self._notes():
            for label in ("hypothesis", "provisional", "tentative", "speculative"):
                with self.subTest(label=label):
                    self.assertNotIn(
                        label,
                        ADMISSIBLE_WEAKER_LABELS,
                        f"{label!r} is admitted by this module; it appears in no "
                        f"note, so it was ranked rather than read",
                    )
                    if label in note.lower():
                        self.fail(
                            f"the record now names {label!r}; re-derive "
                            f"ADMISSIBLE_WEAKER_LABELS from it: {note!r}"
                        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
