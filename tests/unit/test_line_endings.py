"""T-K -- line endings are frozen, and the obvious repair is blocked here.

U1 of `docs/v05_mechanistic_integration_plan.md`. The plan's concern is real:
v0.4's tables are CRLF and the staged literature bundle is LF, so merging staged
rows into a committed table produces a whole-file diff that hides the actual
change from every reviewer.

The conventional fix is `*.tsv text eol=lf` in `.gitattributes`. **Here that fix
is worse than the problem it solves**, and this suite exists to stop a future
round from reaching for it. Two of the four artifacts pinned to the frozen scRNA
evidence root `91f79ed` are CRLF -- `docs/scrna/node_support_evidence.tsv` (1429
lines) and `docs/scrna/node_rna_interpretability.tsv` (28) -- as is
`docs/scrna/node_support_qc.tsv`. Declaring `eol=lf` rewrites those blobs at the
next checkout, breaking the digests T-G exists to enforce, and it does so
without appearing in any commit diff because the rewrite happens on checkout
rather than on edit. Provenance outranks a formatting convention.

So `.gitattributes` says `* -text`: git converts nothing, in either direction,
in any working tree. The merge hazard is then handled where it belongs -- a
staged row merged into a CRLF table is converted to that table's convention at
merge time, which is what actually keeps the diff small.

The counts below are pinned per directory rather than as one total, so a change
is localised to the model or evidence directory that moved. They may SHRINK
deliberately, by a commit that says so; they must never grow by accident.
"""

from __future__ import annotations

import collections
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

#: Extensions whose bytes are not line-oriented. `.svg` is text but is treated
#: as an opaque asset here; none of these participate in the CRLF inventory.
BINARY_SUFFIXES = frozenset({".pdf", ".png", ".gif", ".docx", ".xlsx", ".svg"})

#: Tracked text files that are wholly CRLF, counted by directory. See the module
#: docstring: shrink deliberately, never grow by accident.
PINNED_CRLF_BY_DIRECTORY = {
    "context/literature": 2,
    # `docs/v05_li2026_s2_roundii_screening_annex.tsv`, committed by the v0.5
    # literature pass. It is CRLF because it was extracted from a publisher
    # .xlsx workbook, which is the convention that extraction produced, and the
    # freeze keeps what was committed rather than renormalising it. The pin was
    # not updated when the file landed, so this inventory had been failing since
    # that commit, independently of any later edit; recorded here on 2026-10-22
    # when a separate pdf_manifest line-ending repair surfaced it.
    "docs": 1,
    "docs/scrna": 3,
    # Grown DELIBERATELY by the post-closure PCSK5 correction (OC-001/OC-002).
    # `docs/scrna_corrections/pc6_pcsk5/evidence.tsv` is written in the frozen
    # audit's own format, because the correction re-derives that audit's PCSK6
    # rows and refuses to write unless they reproduce
    # `docs/scrna/node_support_evidence.tsv` byte for byte. Sharing the
    # convention of the file it is checked against is what makes that
    # comparison meaningful, so this entry records a match rather than a drift.
    "docs/scrna_corrections/pc6_pcsk5": 1,
    "input_tables": 1,
    "models/baseline/adoc-core-v0.1.0": 3,
    "models/superset/adoc-literature-superset-v0.3.0": 15,
    "models/superset/adoc-literature-superset-v0.3.0/generated/literature_parity": 3,
    "models/superset/adoc-literature-superset-v0.3.0/generated/minimal_core": 3,
    "models/superset/adoc-literature-superset-v0.3.0/generated/module_expansion_proliferative_feedback": 3,
    "models/superset/adoc-literature-superset-v0.4.0": 14,
    "models/superset/adoc-literature-superset-v0.5.0": 14,
    # Grown DELIBERATELY by U5b, which emits v0.5.1 as a new directory rather
    # than editing v0.5.0: the same 14 tables, each keeping its parent's
    # convention (asserted below). Its one added file is LF, like the shared
    # adjudication file it extends, so it adds nothing here.
    "models/superset/adoc-literature-superset-v0.5.1": 14,
    "models/superset/adoc-literature-superset-v0.5.2": 14,
    # Grown DELIBERATELY by Stage 3, which emits v0.6.0 from v0.5.2 as a new
    # directory: the same 14 tables, each keeping its parent's convention
    # (asserted below).
    "models/superset/adoc-literature-superset-v0.6.0": 14,
}

#: Files with BOTH endings. These are the genuinely dangerous ones -- a row
#: appended in the wrong convention is invisible in review -- so the set is
#: pinned exactly rather than counted.
#:
#: **The set is now empty, and that is a shrink, not a relaxation.**
#: `context/literature/pdf_manifest.tsv` was the one inherited mixed file. U1
#: declined to repair it because it had no substantive reason to touch the file
#: and `docs/v05_line_endings.md` argues against renormalizing a tracked evidence
#: index for a cosmetic reason -- while recording that "a future unit that has a
#: substantive reason to touch that file fixes the endings in the same commit."
#: The 2026-09-18 blocked-source refresh is that unit: it appends PDF-048 and
#: PDF-049, which is exactly the append this pin warns is invisible in review, so
#: it normalized the file to CRLF -- the convention of its header and of its
#: majority -- in the same commit. `context/literature` therefore counts 2 CRLF
#: files above rather than 1. An empty tuple still fails loudly if any file ever
#: becomes mixed again.
PINNED_MIXED_ENDING_FILES: tuple[str, ...] = ()

#: The convention each frozen artifact must keep, byte for byte. These are the
#: files T-G pins to `91f79ed`; a normalization here breaks the evidence root.
FROZEN_EVIDENCE_CONVENTION = {
    "docs/scrna/node_support_evidence.tsv": "crlf",
    "docs/scrna/node_rna_interpretability.tsv": "crlf",
    "docs/scrna/node_support_qc.tsv": "crlf",
    "docs/scrna/node_support_preregistration.md": "lf",
    "docs/scrna/node_support_findings.json": "lf",
    "config/scrna_observation_map.tsv": "lf",
}


def git_available() -> bool:
    """True only when ROOT is itself the top of a git work tree.

    `src/scripts/make_chatgpt_results_bundle.sh` ships `tests/` outside a work tree,
    and a suite that errors there reports a tooling gap as a repository defect.
    But `--git-dir` succeeds from *any* enclosing repository, so a bundle
    unpacked inside an unrelated checkout would have made these assertions read
    that repository's index and report on the wrong files. Comparing
    `--show-toplevel` against ROOT is the distinction actually wanted.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return False
    if result.returncode != 0:
        return False
    return Path(result.stdout.strip()).resolve() == ROOT.resolve()


#: Attribute words that put a path back under git's EOL machinery. Only `-text`
#: is safe: it unsets the attribute outright. `text` and every `text=<value>`
#: form -- `text=auto` above all -- re-enable conversion, and `!text` makes the
#: attribute unspecified, which drops the repository-wide `* -text` for that path
#: and hands the decision back to `core.autocrlf`. A later, more specific rule
#: wins, so any of these can override `* -text` for exactly the frozen evidence
#: files this policy exists to protect.
def renormalizing_attributes(directive: str) -> list[str]:
    """Attributes in one .gitattributes directive that could renormalize.

    Split out so it can be bite-tested against synthetic directives; the
    repository's own file is only one input to it.
    """
    _pattern, *attrs = directive.split()
    bad = []
    for attr in attrs:
        if attr.startswith(("eol=", "text=")) or attr in {"text", "!text"}:
            bad.append(attr)
    return bad


def tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
    ).stdout
    return [p.decode() for p in out.split(b"\0") if p]


def classify(path: Path) -> str:
    data = path.read_bytes()
    if b"\0" in data[:8000]:
        return "binary"
    crlf = data.count(b"\r\n")
    lf = data.count(b"\n") - crlf
    if crlf and lf:
        return "mixed"
    if crlf:
        return "crlf"
    if lf:
        return "lf"
    return "empty"


@unittest.skipUnless(git_available(), "requires a git work tree")
class LineEndingInventoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.kinds: dict[str, str] = {}
        for rel in tracked_files():
            path = ROOT / rel
            if path.suffix.lower() in BINARY_SUFFIXES or not path.is_file():
                continue
            kind = classify(path)
            if kind != "binary":
                cls.kinds[rel] = kind

    def test_crlf_files_are_where_they_were(self) -> None:
        counts = collections.Counter(
            str(Path(rel).parent) for rel, kind in self.kinds.items() if kind == "crlf"
        )
        self.assertEqual(dict(counts), PINNED_CRLF_BY_DIRECTORY)

    def test_mixed_ending_files_are_exactly_the_known_ones(self) -> None:
        mixed = sorted(rel for rel, kind in self.kinds.items() if kind == "mixed")
        self.assertEqual(mixed, sorted(PINNED_MIXED_ENDING_FILES))

    def test_every_frozen_evidence_artifact_keeps_its_convention(self) -> None:
        """The specific files a renormalization would silently break."""
        for rel, expected in sorted(FROZEN_EVIDENCE_CONVENTION.items()):
            with self.subTest(artifact=rel):
                self.assertEqual(classify(ROOT / rel), expected)

    def test_the_scaffold_inherited_the_parent_conventions_exactly(self) -> None:
        """A copy that silently normalises is not a copy."""
        v4 = "models/superset/adoc-literature-superset-v0.4.0"
        v5 = "models/superset/adoc-literature-superset-v0.5.0"
        parent = {
            rel[len(v4) + 1 :]: k
            for rel, k in self.kinds.items()
            if rel.startswith(v4 + "/")
        }
        child = {
            rel[len(v5) + 1 :]: k
            for rel, k in self.kinds.items()
            if rel.startswith(v5 + "/")
        }
        self.assertEqual(child, parent)

    def test_the_increment_inherited_the_parent_conventions_exactly(self) -> None:
        """U5b's v0.5.1 rewrites six of v0.5.0's files; none may change convention.

        A regenerated CRLF table written back as LF would show every row as
        changed and hide the one retirement in `topology.tsv`, which is the
        diff-hiding hazard this module exists for.
        """
        v5 = "models/superset/adoc-literature-superset-v0.5.0"
        v51 = "models/superset/adoc-literature-superset-v0.5.1"
        parent = {
            rel[len(v5) + 1 :]: k
            for rel, k in self.kinds.items()
            if rel.startswith(v5 + "/")
        }
        child = {
            rel[len(v51) + 1 :]: k
            for rel, k in self.kinds.items()
            if rel.startswith(v51 + "/")
        }
        added = {"topology_increment_adjudications.tsv"}
        self.assertEqual(set(child) - set(parent), added)
        self.assertEqual({name: child[name] for name in parent}, parent)
        self.assertEqual(child["topology_increment_adjudications.tsv"], "lf")

    def test_stage3_kept_the_parent_conventions_exactly(self) -> None:
        """v0.6.0 deletes rows from v0.5.2's tables; none may change convention."""
        v52 = "models/superset/adoc-literature-superset-v0.5.2"
        v60 = "models/superset/adoc-literature-superset-v0.6.0"
        parent = {
            rel[len(v52) + 1 :]: k
            for rel, k in self.kinds.items()
            if rel.startswith(v52 + "/")
        }
        child = {
            rel[len(v60) + 1 :]: k
            for rel, k in self.kinds.items()
            if rel.startswith(v60 + "/")
        }
        self.assertEqual(child, parent)


class GitAttributesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        cls.directives = [
            line.split("#", 1)[0].strip()
            for line in cls.text.splitlines()
            if line.split("#", 1)[0].strip()
        ]

    def test_conversion_is_disabled_repository_wide(self) -> None:
        self.assertIn("* -text", self.directives)

    def test_no_directive_would_renormalize_a_committed_file(self) -> None:
        """The guard this suite exists for."""
        for directive in self.directives:
            with self.subTest(directive=directive):
                self.assertEqual(
                    renormalizing_attributes(directive),
                    [],
                    f"{directive!r} puts matching paths back under git's EOL "
                    f"machinery and would rewrite committed bytes at checkout. "
                    f"Use `-text`, or `binary` for binary types; see this "
                    f"module's docstring before adding it.",
                )

    def test_the_guard_rejects_every_way_back_into_conversion(self) -> None:
        """Bite test. An earlier guard checked only `eol=` and a bare `text`.

        `*.tsv text=auto` slipped through it, and because a later, more specific
        rule overrides the repository-wide `* -text`, that one line silently put
        the frozen CRLF evidence artifacts back under conversion while this
        suite stayed green. Every form below is checked so the next variant
        spelling cannot do the same.
        """
        for directive in (
            "*.tsv text=auto",
            "*.tsv text",
            "*.tsv text=lf",
            "*.tsv eol=lf",
            "*.tsv eol=crlf",
            "docs/scrna/*.tsv text=auto eol=lf",
            "* !text",
        ):
            with self.subTest(rejected=directive):
                self.assertNotEqual(renormalizing_attributes(directive), [])

        for directive in ("* -text", "*.pdf binary", "*.png binary", "* -text -diff"):
            with self.subTest(accepted=directive):
                self.assertEqual(renormalizing_attributes(directive), [])

    @unittest.skipUnless(git_available(), "requires a git work tree")
    def test_the_frozen_artifacts_have_no_effective_text_or_eol_attribute(self) -> None:
        """The invariant itself, read from git rather than from the file's text.

        Parsing directives catches the spellings it knows about. This asks git
        what it will actually do to the files that matter, so a bypass through
        some syntax nobody anticipated still fails here.
        """
        paths = sorted(FROZEN_EVIDENCE_CONVENTION)
        result = subprocess.run(
            ["git", "check-attr", "text", "eol", "--", *paths],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
        )
        seen = 0
        for line in result.stdout.splitlines():
            path, attribute, value = (part.strip() for part in line.rsplit(": ", 2))
            with self.subTest(path=path, attribute=attribute):
                expected = "unset" if attribute == "text" else "unspecified"
                self.assertEqual(
                    value,
                    expected,
                    f"git would apply {attribute}={value} to {path}, which is a "
                    f"frozen evidence artifact pinned by T-G. Repair the "
                    f".gitattributes directive, not this assertion.",
                )
            seen += 1
        self.assertEqual(seen, 2 * len(paths))

    @unittest.skipUnless(git_available(), "requires a git work tree")
    def test_git_reports_no_pending_normalization(self) -> None:
        """index eol == worktree eol for every tracked file.

        This is the property that actually matters: a fresh checkout on any
        platform reproduces the committed bytes exactly.
        """
        out = subprocess.run(
            ["git", "ls-files", "--eol", "-z"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        ).stdout
        disagreeing = []
        for entry in out.split(b"\0"):
            if not entry:
                continue
            fields = entry.decode().split()
            index_eol, worktree_eol = fields[0], fields[1]
            if index_eol in {"i/none", "i/-text"} or worktree_eol == "w/none":
                continue
            if index_eol[2:] != worktree_eol[2:]:
                disagreeing.append(entry.decode())
        self.assertEqual(disagreeing, [])


if __name__ == "__main__":
    unittest.main()
