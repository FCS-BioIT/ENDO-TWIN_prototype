"""Phase 2B: the ordering guard that must pass before any candidate KLF12 value is read.

Phase 2A's gate checks that the definition-freeze file precedes the reference
files (RR10) and binds their hashes (RR14). It cannot check that the RULES --
selection, population, comparability route, derivation code -- were frozen
before anyone looked at a candidate's KLF12 values. This guard does, by
content and by commit, never by path alone:

- the repository is a full clone: no shallow boundary, no replace refs, no
  grafts, and git runs with every inherited `GIT_*` variable removed, so the
  history it reads is the real one;
- across the FULL history reachable from HEAD (`--full-history`, so a side
  branch merged with `-s ours` is seen), each rules file (`RULES_FILES`) was
  written by exactly ONE commit: the one that added both. A merge that only
  carries one parent's bytes of the file writes nothing. That commit touches
  nothing else, so the rules pre-registration is its own commit, never
  rewritten, never re-added;
- the working-tree bytes of every rules file equal that commit's bytes;
- `owner_decisions.json` was written by exactly one commit, a proper ancestor
  of the rules commit, and is unchanged since;
- the rules pin every file in `REQUIRED_PINS` (the import closure of the
  derivation and the value reader) by repository-relative path, and each still
  hashes to its pin. A pin cannot be absolute, contain `..`, be a symlink or
  resolve outside the repository.

Amendments (`preregistration_amendment_NN.json/.md`) are allowed only
before any value-derived work: each is its own commit, written once, built
on the stage before it with nothing else written to docs/phase2b/ in between.
The latest one's pins govern. The rules file itself is never rewritten.

`values.open_reference_values` calls `assert_rules_frozen` first and refuses to
read anything if it raises.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath

OUT_DIR = Path("docs/phase2b")
OWNER_DECISIONS = OUT_DIR / "owner_decisions.json"
PREREG_MD = OUT_DIR / "preregistration.md"
PREREG_JSON = OUT_DIR / "preregistration.json"
RULES_FILES = (PREREG_JSON, PREREG_MD)

#: The dt_adoc modules imported by the derivation and the value reader, plus the
#: committed data they read. `tests/unit/test_phase2b_contract.py` recomputes
#: the import closure in a fresh interpreter and requires it to equal this set.
REQUIRED_PINS = (
    "docs/phase2b/adoc_identity_denylist.json",
    "docs/phase2b/owner_decisions.json",
    "src/dt_adoc/model/topology.py",
    "src/dt_adoc/personalization/phase2a_contract.py",
    "src/dt_adoc/personalization/phase2b/derivation.py",
    "src/dt_adoc/personalization/phase2b/guard.py",
    "src/dt_adoc/personalization/phase2b/identity.py",
    "src/dt_adoc/personalization/phase2b/qualification.py",
    "src/dt_adoc/personalization/phase2b/values.py",
    "src/dt_adoc/scrna/klf12_state.py",
    "src/dt_adoc/scrna/node_support_contract.py",
    "src/dt_adoc/scrna/verify_rds.py",
)


class OrderingError(RuntimeError):
    """The rules are not provably frozen; no candidate value may be read."""


def _environment() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    return env


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "--no-replace-objects", "-C", str(root), *args],
        capture_output=True,
        check=False,
        env=_environment(),
    )


def _git(root: Path, *args: str) -> str:
    done = _run(root, *args)
    if done.returncode != 0:
        raise OrderingError(
            f"git {' '.join(args)} failed: {done.stderr.decode().strip()}"
        )
    return done.stdout.decode().strip()


def _blob(root: Path, commit: str, relative: Path) -> bytes:
    done = _run(root, "show", f"{commit}:{relative.as_posix()}")
    if done.returncode != 0:
        raise OrderingError(f"{relative} is not in commit {commit}")
    return done.stdout


def _assert_real_history(root: Path) -> None:
    if _git(root, "rev-parse", "--is-shallow-repository") != "false":
        raise OrderingError(
            "a shallow clone hides history; the ordering cannot be proven"
        )
    if _git(root, "for-each-ref", "refs/replace/"):
        raise OrderingError(
            "replace refs rewrite history; the ordering cannot be proven"
        )
    grafts = Path(_git(root, "rev-parse", "--git-path", "info/grafts"))
    if (grafts if grafts.is_absolute() else root / grafts).exists():
        raise OrderingError(
            "a grafts file rewrites history; the ordering cannot be proven"
        )


def _tree_entry(root: Path, commit: str, relative: Path) -> str | None:
    """The mode, type and object id of `relative` in `commit`, or None if absent."""
    entry = _git(root, "ls-tree", "--full-tree", commit, "--", relative.as_posix())
    return entry.split("\t", 1)[0] if entry else None


def _writes(
    root: Path, commit: str, relative: Path, *, inherited_absence: bool = False
) -> bool:
    """Whether `commit` wrote `relative`, rather than carrying a parent's bytes.

    A merge whose entry for the file (mode and blob) is exactly one of its
    parents' wrote nothing: those bytes are that parent's, and every commit
    that ever changed them is itself listed. A merge that holds bytes none of
    its parents holds (an evil merge), or drops the file, did write it. A
    non-merge commit listed by `git log -- <path>` always wrote it. This is
    amendment 07's rule, and the one `_only_commit` applies to frozen files.

    `inherited_absence` is for the between-amendments check only (amendment
    12): there a merge that lacks the file exactly as one of its parents
    lacks it carries that parent's deletion and wrote nothing; a merge that
    drops a file every parent holds still wrote it.
    """
    parents = _git(root, "rev-list", "--parents", "-n", "1", commit).split()[1:]
    if len(parents) < 2:
        return True
    entry = _tree_entry(root, commit, relative)
    if entry is None and not inherited_absence:
        return True
    return all(_tree_entry(root, parent, relative) != entry for parent in parents)


def _only_commit(root: Path, relative: Path) -> str:
    """The single commit, anywhere in the full history of EVERY ref, that wrote `relative`.

    `--all` so a draft left on an unmerged branch or a tag counts too. History
    rewritten before it ever reached a ref (an amend, a reset) is invisible to
    any local check; only an external anchor such as a pushed commit closes it.

    `--full-history` also lists every merge not identical to all its parents
    for the file, including an ordinary `--no-ff` merge of the branch that
    froze it (amendment 07); such a merge counts only if it wrote the file
    (`_writes`). A side branch's own commits are listed regardless, so a
    draft hidden by `merge -s ours` is still seen.
    """
    touched = [
        commit
        for commit in _git(
            root,
            "log",
            "--all",
            "--full-history",
            "--format=%H",
            "--",
            relative.as_posix(),
        ).splitlines()
        if _writes(root, commit, relative)
    ]
    if not touched:
        raise OrderingError(f"{relative} was never committed")
    if len(touched) != 1:
        raise OrderingError(
            f"{relative} was written by {len(touched)} commits; a frozen file is written once"
        )
    return touched[0]


#: What `docs/phase2b/` may hold before the rules commit: value-blind inputs.
PRE_RULES_FILES = frozenset(
    {
        "docs/phase2b/adoc_identity_denylist.json",
        "docs/phase2b/candidate_inventory.tsv",
        "docs/phase2b/owner_decisions.json",
        "docs/phase2b/phase2a_audit.json",
    }
)


def _assert_no_earlier_draft(root: Path, commit: str) -> None:
    """No commit before the rules wrote anything else under docs/phase2b/, and no
    commit anywhere touched a case variant of a rules path.

    A draft of the rules at another path would otherwise be invisible to the
    exact-path checks above. A draft kept outside docs/phase2b/ is not
    detectable mechanically and is excluded by review of the history.
    """
    stray: set[str] = set()
    for other in _git(
        root, "rev-list", "--all", "--full-history", "--", OUT_DIR.as_posix()
    ).splitlines():
        if other == commit or _is_ancestor(root, commit, other):
            continue  # the rules commit and everything built on it
        names = _git(
            root,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "--root",
            "-m",
            other,
        )
        stray |= {
            p for p in names.splitlines() if p.startswith(f"{OUT_DIR.as_posix()}/")
        } - PRE_RULES_FILES
    if stray:
        raise OrderingError(
            f"docs/phase2b/ held {sorted(stray)} outside the rules' own history"
        )
    rules = {rel.as_posix().casefold(): rel.as_posix() for rel in RULES_FILES}
    everything = _git(
        root, "log", "--all", "--full-history", "--format=", "--name-only"
    )
    variants = sorted(
        {
            p
            for p in everything.splitlines()
            if p.casefold() in rules and p not in rules.values()
        }
    )
    if variants:
        raise OrderingError(
            f"case variants of the rules paths were committed: {variants}"
        )


def _unchanged(root: Path, commit: str, relative: Path) -> None:
    path = root / relative
    if path.is_symlink() or not path.is_file():
        raise OrderingError(f"{relative} is missing from the working tree or is a link")
    if path.read_bytes() != _blob(root, commit, relative):
        raise OrderingError(f"{relative} differs from its frozen bytes in {commit}")


def _is_ancestor(root: Path, earlier: str, later: str) -> bool:
    return _run(root, "merge-base", "--is-ancestor", earlier, later).returncode == 0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pinned_path(root: Path, relative: object) -> Path:
    if not isinstance(relative, str) or not relative:
        raise OrderingError(f"pin {relative!r} is not a path")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or "\\" in relative:
        raise OrderingError(f"pin {relative!r} must be repository-relative")
    path = root / pure
    if (
        path.is_symlink()
        or not path.is_file()
        or not path.resolve().is_relative_to(root)
    ):
        raise OrderingError(
            f"pin {relative!r} is not a regular file inside the repository"
        )
    return path


#: The one docs/phase2b/ output that may be regenerated between two rule
#: stages: the value-blind Phase-2A audit, which a Phase-2A schema change
#: approved in an amendment must be able to re-record.
VALUE_BLIND_BETWEEN_STAGES = frozenset({"docs/phase2b/phase2a_audit.json"})


def amendment_files(number: int) -> tuple[Path, Path]:
    stem = f"preregistration_amendment_{number:02d}"
    return OUT_DIR / f"{stem}.json", OUT_DIR / f"{stem}.md"


_AMENDMENT = re.compile(
    r"docs/phase2b/preregistration_amendment_([0-9]{2})\.(?:json|md)"
)


def _single_file_commit(root: Path, files: tuple[Path, ...], what: str) -> str:
    """The one commit that wrote exactly `files`, alone, not a merge."""
    commits = {rel: _only_commit(root, rel) for rel in files}
    if len(set(commits.values())) != 1:
        raise OrderingError(
            f"the {what} files were written in different commits: {commits}"
        )
    commit = commits[files[0]]
    if len(_git(root, "rev-list", "--parents", "-n", "1", commit).split()) > 2:
        raise OrderingError(f"the {what} commit {commit} is a merge")
    touched = set(
        _git(
            root, "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", commit
        ).splitlines()
    )
    if touched != {rel.as_posix() for rel in files}:
        raise OrderingError(
            f"the {what} commit {commit} is not its own commit; it touches {sorted(touched)}"
        )
    for rel in files:
        _unchanged(root, commit, rel)
    return commit


def _amendments(root: Path, rules_commit: str, head: str) -> list[tuple[int, str]]:
    """Every amendment, in order: each its own commit, each built directly on the
    previous stage with nothing else written to docs/phase2b/ in between, so
    every amendment precedes any value-derived artifact.
    """
    everything = _git(
        root, "log", "--all", "--full-history", "--format=", "--name-only"
    )
    numbers = sorted(
        {
            int(m.group(1))
            for p in everything.splitlines()
            if (m := _AMENDMENT.fullmatch(p))
        }
        | {
            int(m.group(1))
            for p in (root / OUT_DIR).glob("preregistration_amendment_*")
            if (m := _AMENDMENT.fullmatch(p.relative_to(root).as_posix()))
        }
    )
    if numbers != list(range(1, len(numbers) + 1)):
        raise OrderingError(
            f"amendments must be numbered 01, 02, ... without gaps: {numbers}"
        )
    chain: list[tuple[int, str]] = []
    previous = rules_commit
    for number in numbers:
        commit = _single_file_commit(
            root, amendment_files(number), f"amendment {number:02d}"
        )
        if commit == previous or not _is_ancestor(root, previous, commit):
            raise OrderingError(
                f"amendment {number:02d} does not build on the stage before it"
            )
        if not _is_ancestor(root, commit, head):
            raise OrderingError(f"amendment {number:02d} is not an ancestor of HEAD")
        between = _git(
            root,
            "log",
            "--full-history",
            "--format=%H",
            f"{previous}..{commit}",
            "--",
            OUT_DIR.as_posix(),
        ).splitlines()
        written = set()
        for other in between:
            if other != commit:
                # -m: without it diff-tree lists nothing for a merge, so a merge
                # that itself wrote under docs/phase2b/ went unseen (amendment
                # 10). -m lists what a merge carries from EITHER parent, so
                # each path is kept only if the merge wrote it (`_writes`,
                # with an inherited absence not a write: amendment 12).
                written |= {
                    p
                    for p in _git(
                        root,
                        "diff-tree",
                        "--no-commit-id",
                        "--name-only",
                        "-r",
                        "-m",
                        other,
                    ).splitlines()
                    if p.startswith(f"{OUT_DIR.as_posix()}/")
                    and _writes(root, other, Path(p), inherited_absence=True)
                }
        if commit not in between or written - VALUE_BLIND_BETWEEN_STAGES:
            raise OrderingError(
                f"docs/phase2b/ was written between the stage before amendment "
                f"{number:02d} and it; an amendment after value-derived work is a deviation"
            )
        chain.append((number, commit))
        previous = commit
    return chain


def assert_rules_frozen(
    root: Path, *, required_pins: tuple[str, ...] | None = None
) -> dict[str, str]:
    """Raise `OrderingError` unless the rules are provably frozen; return the proof.

    `required_pins` defaults to `REQUIRED_PINS`, read at call time.
    """
    root = root.resolve()
    required = REQUIRED_PINS if required_pins is None else required_pins
    _assert_real_history(root)
    head = _git(root, "rev-parse", "HEAD")
    commit = _single_file_commit(root, RULES_FILES, "rules")
    if not _is_ancestor(root, commit, head):
        raise OrderingError(f"the rules commit {commit} is not an ancestor of HEAD")
    _assert_no_earlier_draft(root, commit)

    decisions = _only_commit(root, OWNER_DECISIONS)
    if decisions == commit or not _is_ancestor(root, decisions, commit):
        raise OrderingError(
            "owner_decisions.json must be committed strictly before the rules"
        )
    _unchanged(root, decisions, OWNER_DECISIONS)

    chain = _amendments(root, commit, head)
    governing = amendment_files(chain[-1][0])[0] if chain else PREREG_JSON
    rules = json.loads((root / governing).read_text(encoding="utf-8"))
    pinned = rules.get("pinned_implementation_sha256")
    if not isinstance(pinned, dict):
        raise OrderingError("the rules pin no implementation")
    missing = sorted(set(required) - set(pinned))
    if missing:
        raise OrderingError(f"the rules do not pin {missing}")
    for relative, digest in sorted(pinned.items()):
        if sha256(_pinned_path(root, relative)) != digest:
            raise OrderingError(f"{relative} no longer hashes to its pinned sha256")
    return {
        "rules_commit": commit,
        "owner_decisions_commit": decisions,
        "head": head,
        "preregistration_json_sha256": sha256(root / PREREG_JSON),
        "preregistration_md_sha256": sha256(root / PREREG_MD),
        "amendments": ";".join(f"{n:02d}:{c}" for n, c in chain),
        "governing_pins": governing.as_posix(),
    }
