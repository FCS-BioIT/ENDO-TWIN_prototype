# Line endings: why v0.5 freezes them instead of normalizing them

**Unit:** U1 of `docs/v05_mechanistic_integration_plan.md` (test T-K).
**Decision:** `.gitattributes` declares `* -text`. Nothing is normalized, now or
at any future checkout. **`*.tsv text eol=lf` must not be added.**
**Enforced by:** `tests/unit/test_line_endings.py`.

---

## 1. The problem T-K was written for

The plan states it at §12, T-K:

> v0.4 tables are CRLF, the staged bundle LF, no `.gitattributes`. Merging
> staged rows will otherwise produce whole-file diffs that hide the real change
> from every reviewer. Settle in U1.

That is a real hazard and it is correctly described. The reviewer-facing failure
mode — a one-row change arriving as a 1,400-line diff — is exactly the kind of
thing that gets waved through.

## 2. Why the conventional fix is wrong *here*

The standard remedy is a `.gitattributes` line such as `*.tsv text eol=lf`,
which normalizes every table to LF. Applied to this repository it would rewrite
committed bytes, and the files it would rewrite are the wrong ones.

The scRNA audit's evidence root is `91f79ed`. Plan §12 (T-G) pins four
artifacts there, byte for byte. **Two of the four are CRLF:**

| artifact | tier | endings | lines |
|---|---|---|---|
| `docs/scrna/node_support_evidence.tsv` | T-G tier 1 | **CRLF** | 1,429 |
| `docs/scrna/node_rna_interpretability.tsv` | T-G tier 1 | **CRLF** | 28 |
| `docs/scrna/node_support_preregistration.md` | T-G tier 1 | LF | 729 |
| `config/scrna_observation_map.tsv` | T-G tier 1 | LF | 60 |
| `docs/scrna/node_support_qc.tsv` | T-G tier 2 | **CRLF** | 18 |
| `docs/scrna/node_support_findings.json` | T-G tier 2 | LF | 3,187 |

A blanket `eol=lf` changes the bytes of the first, second and fifth rows. Those
bytes are what T-G's digests are taken over, and those digests are the whole
mechanism by which the frozen audit stays frozen. The rule would therefore:

1. **break the evidence root** — every `91f79ed` digest over a CRLF artifact
   stops matching;
2. **do it invisibly** — the rewrite happens at *checkout*, not at edit, so it
   appears in no commit diff. A reviewer reading the `.gitattributes` commit
   sees one added line and no artifact changes at all;
3. **invite the worst repair** — the next round, facing a red T-G, re-pins the
   artifacts to the new digests. The test goes green, the evidence root is gone,
   and nothing in the history says so.

Point 3 is the shape `AGENTS.md` and the harness policy both name: repairing a
review finding by moving the rule rather than the code. It arrives disguised as
housekeeping, which is what makes it worth writing down.

Note also that the convention is not uniform even *within* the frozen set —
`config/scrna_observation_map.tsv` is LF while its three sibling tables are
CRLF. There is no blanket rule that leaves all six untouched.

## 3. What was done instead

`.gitattributes`:

```
* -text
```

`-text` means git performs no end-of-line conversion in either direction. The
bytes in the index are the bytes on disk, on every platform. Verified when the
attribute landed: **every tracked file had identical worktree and index blob
digests**, and `git ls-files --eol` reported `i/crlf w/crlf` and `i/lf w/lf`
unchanged throughout. The standing form of that check is
`test_git_reports_no_pending_normalization`, which asserts it on every run
rather than at one moment.

*A bare file count was given here and was wrong.* It was taken mid-change,
before the v0.5 scaffold was staged, and it went stale in the same commit that
wrote it. Counts that no test pins do not belong in this document; see §5.

Binary types (`*.pdf`, `*.png`, `*.gif`, `*.docx`, `*.xlsx`) are additionally
declared `binary` so git does not attempt textual diffs or merges on them. This
is presentational and changes no bytes; `-text` already prevented conversion.
It does, however, protect `data/` — which `AGENTS.md` declares immutable source
evidence — against a text-mode checkout on another platform, without editing
anything under `data/`.

## 4. So how is the actual merge hazard handled?

By convention at merge time, not by rewriting history:

> **A staged row merged into a committed table is converted to that table's
> existing convention as part of the merge.**

This is what actually delivers T-K's goal. Normalizing the whole file makes the
diff enormous once, permanently, and breaks provenance; converting the incoming
rows makes every such diff exactly as large as the change. The staged bundles
under `context/literature/staging/` are LF; the tables they feed are mostly
CRLF; the conversion is the merging unit's job and is cheap.

## 5. The inventory, pinned

`tests/unit/test_line_endings.py` pins CRLF counts **per directory** rather than
as one total, so a change is localised to the model or evidence directory that
moved. At U1 it pinned **60 CRLF files** across ten directories and **1 mixed**;
after the 2026-09-18 normalization described below it pins **61** and **0**.

**Only test-pinned figures are quoted here, deliberately.** An earlier revision
also gave totals for "tracked text files" and "tracked files". Both were wrong
and both went stale inside the commit that wrote them, because nothing asserted
them and "tracked text file" was never defined against the suite's own
`BINARY_SUFFIXES` exclusion. A number in prose that no test defends is a number
that will disagree with the enforced inventory and leave a reader unable to tell
which described the commit. Read the pinned dictionary in the test for the
current inventory.

Counts may **shrink** — by a commit that says which file was converted and why —
and must never grow by accident.

### Mixed-ending files

**The set is now empty.** Mixed files are the genuinely dangerous case, because a
row appended in the wrong convention is invisible in review, so the set is
pinned exactly rather than counted, and `PINNED_MIXED_ENDING_FILES` is an empty
tuple that still fails loudly if any file becomes mixed again.

One tracked file used to carry both conventions: `context/literature/pdf_manifest.tsv`
(27 CRLF lines, 21 LF as U1 found it).

**U1 recorded it rather than repairing it.** It was outside U1's scope, and
normalizing a tracked evidence index for a cosmetic reason is the same category of
change this document argues against. It was flagged so that a future unit with a
substantive reason to touch the file would fix the endings in the same commit.

**That happened on 2026-09-18.** The blocked-source refresh
(`docs/curation_increment_08_blocked_sources.md`) appended `PDF-048` and `PDF-049`
to that file — which is exactly the append this section warns is invisible in
review — and normalized it to **CRLF**, the convention of its header and of its
majority, in the same commit. `context/literature` therefore counts **2** CRLF
files rather than 1. That is a shrink of the mixed set, stated by the commit that
made it, which is what this document asks for; the CRLF count grew only because a
mixed file became a wholly-CRLF one, not because any LF file was converted.

## 6. What the tests assert

`tests/unit/test_line_endings.py`:

- CRLF files are where they were, per directory;
- the mixed-ending set is exactly the pinned set, which is now **empty**;
- each of the six frozen artifacts above keeps its exact convention;
- the v0.5 scaffold inherited v0.4's conventions file for file — a copy that
  silently normalises is not a copy;
- `.gitattributes` contains `* -text`, and **no directive re-enables git's EOL
  machinery in any form**: `eol=*`, bare `text`, any `text=*` (including
  `text=auto`), and `!text` are all rejected. This is the guard: it fails the
  build rather than the evidence root, and every rejected form is exercised.

  *Hardened after external review.* The first version of this guard rejected
  only `eol=` and a bare `text`. **`*.tsv text=auto` went straight through it** —
  and because a later, more specific rule overrides the repository-wide
  `* -text`, that single line put the frozen CRLF artifacts back under
  conversion while the suite stayed green. Reproduced before fixing:
  `git check-attr text` on `docs/scrna/node_support_evidence.tsv` went from
  `unset` to `auto` with the suite still passing. `!text` is rejected for the
  same reason — it makes the attribute unspecified, which drops `* -text` for
  that path and hands the decision back to `core.autocrlf`.

- **The effective attributes are asserted, not just the directive text.**
  `git check-attr text eol` is run against each of the six frozen artifacts and
  must report `text: unset` and `eol: unspecified`. Parsing directives catches
  the spellings it knows about; this asks git what it will actually do, so a
  bypass through some syntax nobody anticipated still fails.
- `git ls-files --eol` reports no file whose index and worktree endings differ,
  so a fresh checkout reproduces committed bytes exactly.

The assertions that read the git index are skipped where there is no work tree,
because `scripts/make_chatgpt_results_bundle.sh` ships `tests/` outside one and a
suite that errors there reports a tooling gap as a repository defect. The
`.gitattributes` guard itself reads the file from disk and always runs.

## 7. Two things deliberately not done

- **`pixi.lock` is not marked `-diff`.** An earlier draft of `.gitattributes`
  suppressed its diff as housekeeping. That was wrong here: it reduces a
  dependency change to `Binary files differ`, and this repository's provenance
  contract records software versions and its review gate reads diffs. Hiding the
  lock file from review to keep diffs tidy trades exactly the wrong thing.
- **No `merge` driver is declared for the CRLF tables.** The convention in §4 is
  a rule for the unit doing the merge, not automation. Automating it would mean
  a driver that rewrites incoming content, which is the class of silent
  transformation this document argues against.
