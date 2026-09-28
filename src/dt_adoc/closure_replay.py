"""Replay the closed Phase 1B / 2A / 2B analyses against their closure-time models/.

Phases 1B, 2A and 2B each guard the *whole* ``models/`` tree:

* Phase 1B records a tree digest and the set of superset directories;
* Phase 2A's gate G7 requires the live tree to equal Phase 1B's digest;
* Phase 2B's audit counts every file under ``models/`` that did not exist at its
  base commit as a frozen-artifact change.

Read as closure-time invariants, those guards prove that the model tree those
analyses used did not change while they ran. They are not a permanent ban on
adding later, explicitly versioned models. The closed code and its committed
outputs are frozen: ``phase2a_contract.py`` is bound by sha256 in Phase 2B's
audit, and no historical record may be rewritten to accommodate a new version.
So the guards are not edited. Instead, the closed phases are reproduced against
their frozen snapshot, and this module builds that snapshot:

* every top-level entry of the repository, symlinked, exactly as the
  generator-determinism test's shadow root does;
* ``models/`` as a real copy of the closure-time model tree. That is every file
  except the superset versions created after closure;
* a temporary git index without those versions, because Phase 2B enumerates
  frozen paths through ``git ls-files --cached``. The caller passes it to git as
  ``GIT_INDEX_FILE``.

The closure-time model set is fixed and complete. It is the four superset
directories that existed when Phase 1B was closed. Nothing here names a later
version, so every future version is outside the snapshot without an exception
of its own. ``tests/unit/test_closure_replay.py`` proves that the snapshot is
byte-identical to the tree the closures recorded.

Phase 2B's audit freezes more than ``models/``. Under ``FROZEN_PREFIXES``
(``personalization/phase2b/audit.py``) it also freezes ``config/``,
``docs/scrna/``, ``docs/experiments/``, ``docs/phase1b_closure/``,
``docs/phase2a/`` and ``phase2a_contract.py``. Those are edited in place rather
than added to by version, so they cannot be reconstructed by exclusion the way
``models/`` is. The snapshot therefore takes them, as real files and as git
index entries, from the commit that closed Phase 2B, ``PHASE2B_CLOSURE_COMMIT``.
A snapshot alone would hide a later edit to a closed input, so the live tree is
held to an explicit allowance (``undeclared_drift``). Under those paths it may
differ from the closure commit only by:

* a declared post-closure file (``POST_CLOSURE_FILES``); or
* a declared provenance-only regeneration, where only named JSON fields differ
  (``PROVENANCE_ONLY_REGENERATIONS``).

Anything else is reported. ``tests/unit/test_closure_replay.py`` requires that
report to be empty.

Consequence, stated so it is not surprising: running ``pixi run
build-phase2a-contract`` (or the Phase 1B / 2B builders) directly on the live,
post-closure tree fails their whole-tree guard by design. Reproduce them with
``pixi run replay-closed-phases``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

#: models/superset/ when Phase 1B was closed (tests/unit/test_phase1b_closure.py
#: MODEL_DIRECTORIES); Phases 2A and 2B were closed on the same tree.
CLOSURE_SUPERSET_VERSIONS = frozenset(
    {
        "adoc-literature-superset-v0.3.0",
        "adoc-literature-superset-v0.4.0",
        "adoc-literature-superset-v0.5.0",
        "adoc-literature-superset-v0.5.1",
    }
)
#: The closed-phase builders, as pixi task -> module.
CLOSED_PHASE_BUILDERS = {
    "build-phase1b-closure": "dt_adoc.experiments.phase1b_closure",
    "build-phase2a-contract": "dt_adoc.personalization.phase2a_contract",
    "build-phase2b-audit": "dt_adoc.personalization.phase2b.audit",
}
SUPERSET = Path("models/superset")

#: The commit that closed Phase 2B ("docs(phase2b): close Phase 2B as
#: NO_SUITABLE_REFERENCE"). Its content under ``CLOSURE_FROZEN_PATHS`` is the
#: content all three closed phases ran on.
PHASE2B_CLOSURE_COMMIT = "97f88f55ce62e2adca23f631de3ad8e1270ad3e6"
#: Phase 2B's ``FROZEN_PREFIXES`` other than ``models/``, which is handled above.
#: The test suite requires the two to agree.
CLOSURE_FROZEN_PATHS = (
    "docs/phase2a/",
    "docs/phase1b_closure/",
    "docs/scrna/",
    "docs/experiments/",
    "config/",
    "src/dt_adoc/personalization/phase2a_contract.py",
)
#: Files added under ``CLOSURE_FROZEN_PATHS`` after closure, with the reason each
#: may exist. None is read by a closed phase.
POST_CLOSURE_FILES = {
    "config/intervention_library.tsv": (
        "intervention library of the intervention-layer refactor "
        "(docs/intervention_layer_refactor_plan.md)"
    ),
    "config/direct_effect_adjudications.tsv": (
        "effect-level approvals of direct_supported_effect library rows "
        "(docs/o8b_direct_effect_governance.md)"
    ),
    "config/direct_effect_target_policy.tsv": (
        "target-role policy for direct_supported_effect rows "
        "(docs/o8b_direct_effect_governance.md)"
    ),
    "config/node_entity_map.tsv": (
        "reading of each model version's node dictionary into entities, for the "
        "Stage 4b admission checks C3-C7 (docs/stage4b_direct_admission.md)"
    ),
    "config/direct_effect_target_declarations.tsv": (
        "intervention-level target declarations of direct_supported_effect "
        "interventions (docs/stage4b_direct_admission.md)"
    ),
    "config/protocols_markerless.yaml": (
        "protocol rows for the superset versions without intervention-marker "
        "nodes (docs/intervention_layer_stage3.md); config/protocols.yaml is not "
        "edited"
    ),
    "config/scrna_observation_map_corrections.tsv": (
        "post-closure corrections applied by live consumers only "
        "(dt_adoc.scrna.observation_corrections, docs/scrna_corrections/README.md); "
        "config/scrna_observation_map.tsv is not edited"
    ),
}
#: Files under ``CLOSURE_FROZEN_PATHS`` regenerated after closure whose only
#: permitted change is provenance: the dotted JSON fields that may differ from
#: the closure commit. Every other byte of meaning must be the closure's.
PROVENANCE_ONLY_REGENERATIONS = {
    "docs/scrna/klf12_conditioning_settings.json": (
        "provenance.git_commit",
        "provenance.git_tree_dirty",
        "provenance.implementation_digest",
        "provenance.implementation_files",
    ),
}


def post_closure_versions(root: Path) -> list[str]:
    """Superset directories that did not exist when the phases were closed."""
    superset = root / SUPERSET
    return sorted(
        p.name
        for p in superset.iterdir()
        if p.is_dir() and p.name not in CLOSURE_SUPERSET_VERSIONS
    )


def _copy_closure_models(root: Path, destination: Path) -> None:
    later = set(post_closure_versions(root))

    def ignore(directory: str, names: list[str]) -> set[str]:
        if Path(directory).resolve() == (root / SUPERSET).resolve():
            return {n for n in names if n in later}
        return {n for n in names if n == "__pycache__"}

    shutil.copytree(root / "models", destination / "models", ignore=ignore)


def _closure_index(root: Path, index: Path) -> None:
    env = {**os.environ, "GIT_INDEX_FILE": str(index)}
    subprocess.run(["git", "-C", str(root), "read-tree", "HEAD"], env=env, check=True)
    for version in post_closure_versions(root):
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "rm",
                "-r",
                "--cached",
                "--quiet",
                "--ignore-unmatch",
                "--",
                (SUPERSET / version).as_posix(),
            ],
            env=env,
            check=True,
        )
    # The frozen paths are indexed as the closure commit had them, so a file
    # added after closure is neither in the view nor in its index.
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "rm",
            "-r",
            "--cached",
            "--quiet",
            "--ignore-unmatch",
            "--",
            *CLOSURE_FROZEN_PATHS,
        ],
        env=env,
        check=True,
    )
    records = "".join(
        f"{mode} {sha}\t{path}\n" for mode, sha, path in _closure_entries(root)
    )
    subprocess.run(
        ["git", "-C", str(root), "update-index", "--index-info"],
        input=records.encode("utf-8"),
        env=env,
        check=True,
    )


def _live_frozen_files(root: Path) -> set[str]:
    """Every live file under the frozen paths: tracked, untracked and gitignored."""
    listed: set[str] = set()
    for extra in (
        [],
        ["--others", "--exclude-standard"],
        ["--others", "--ignored", "--exclude-standard"],
    ):
        listed |= set(
            _git_bytes(
                root, "ls-files", "--cached", *extra, "--", *CLOSURE_FROZEN_PATHS
            )
            .decode("utf-8")
            .splitlines()
        )
    return {
        path for path in listed if (root / path).is_file() or (root / path).is_symlink()
    }


def _without(payload: object, dotted: str) -> None:
    *parents, leaf = dotted.split(".")
    for key in parents:
        if not isinstance(payload, dict) or key not in payload:
            return
        payload = payload[key]
    if isinstance(payload, dict):
        payload.pop(leaf, None)


def undeclared_drift(root: Path) -> list[str]:
    """Live differences from the closure commit under the frozen paths that are not
    declared in ``POST_CLOSURE_FILES`` or ``PROVENANCE_ONLY_REGENERATIONS``."""
    import json

    root = root.resolve()
    closure = {path: sha for _, sha, path in _closure_entries(root)}
    report = []
    for path in sorted(set(closure) | _live_frozen_files(root)):
        live = root / path
        if path not in closure:
            if path not in POST_CLOSURE_FILES or live.is_symlink():
                report.append(f"added: {path}")
            continue
        if not live.is_file() or live.is_symlink():
            report.append(f"missing or linked: {path}")
            continue
        frozen = _git_bytes(root, "cat-file", "blob", closure[path])
        current = live.read_bytes()
        if current == frozen:
            continue
        fields = PROVENANCE_ONLY_REGENERATIONS.get(path)
        if fields is None:
            report.append(f"changed: {path}")
            continue
        before, after = json.loads(frozen), json.loads(current)
        for dotted in fields:
            _without(before, dotted)
            _without(after, dotted)
        if before != after:
            report.append(f"changed beyond provenance: {path}")
    for path in POST_CLOSURE_FILES:
        if path in closure:
            report.append(f"declared as added but present at closure: {path}")
    return report


def _git_bytes(root: Path, *args: str, env: dict[str, str] | None = None) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=True,
        env={**os.environ, **(env or {})},
    ).stdout


def _closure_entries(root: Path) -> list[tuple[str, str, str]]:
    """(mode, blob sha, path) of every closure-commit file under the frozen paths."""
    listing = _git_bytes(
        root, "ls-tree", "-r", "-z", PHASE2B_CLOSURE_COMMIT, "--", *CLOSURE_FROZEN_PATHS
    )
    entries = []
    for record in listing.decode("utf-8").split("\0"):
        if not record:
            continue
        meta, path = record.split("\t", 1)
        mode, kind, sha = meta.split()
        if kind != "blob":
            raise ValueError(f"unexpected {kind} at {path} in the closure commit")
        entries.append((mode, sha, path))
    return entries


def _copy_closure_frozen_paths(
    root: Path, destination: Path, carved: tuple[Path, ...]
) -> None:
    """Write the closure commit's frozen files as real files; outputs stay absent."""
    for mode, sha, path in _closure_entries(root):
        if Path(path) in carved:
            continue
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_git_bytes(root, "cat-file", "blob", sha))
        if mode == "100755":
            target.chmod(0o755)


def _mirror(
    source: Path, destination: Path, relative: Path, carved: tuple[Path, ...]
) -> None:
    """Symlink every entry; make real directories only on the way to a carved path.

    A carved path is left absent, never symlinked. Builder outputs are carved so
    that a builder writing one cannot write through into the checked-out tree
    (the same rule as the generator-determinism test's shadow root). The frozen
    paths are carved so that the closure commit's copies can take their place.
    """
    destination.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source.iterdir()):
        here = relative / entry.name
        if here == Path("models") or here in carved:
            continue
        if entry.is_dir() and any(path.is_relative_to(here) for path in carved):
            _mirror(entry, destination / entry.name, here, carved)
        else:
            (destination / entry.name).symlink_to(entry)


def build_view(
    root: Path, destination: Path, carved: tuple[Path, ...] = ()
) -> tuple[Path, Path]:
    """Write the closure-time view under ``destination``: (view root, git index).

    ``carved`` output paths are left absent so a builder can write them.
    """
    root = root.resolve()
    if any(Path(p).is_relative_to("models") for p in carved):
        raise ValueError("a closed-phase builder must not write under models/")
    view = destination / "closure_root"
    outputs = tuple(Path(p) for p in carved)
    frozen = tuple(Path(p) for p in CLOSURE_FROZEN_PATHS)
    _mirror(root, view, Path(), outputs + frozen)
    _copy_closure_models(root, view)
    _copy_closure_frozen_paths(root, view, outputs)
    index = destination / "closure.index"
    _closure_index(root, index)
    return view, index


@contextmanager
def closure_view(
    root: Path, carved: tuple[Path, ...] = ()
) -> Iterator[tuple[Path, dict[str, str]]]:
    """A temporary closure-time view and the environment git must run under."""
    with tempfile.TemporaryDirectory(prefix="closure-replay-") as tmp:
        view, index = build_view(root, Path(tmp), carved)
        yield view, {"GIT_INDEX_FILE": str(index)}


@contextmanager
def git_index(env: dict[str, str]) -> Iterator[None]:
    """Point in-process git subprocesses at the closure index, then restore."""
    previous = os.environ.get("GIT_INDEX_FILE")
    os.environ.update(env)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("GIT_INDEX_FILE", None)
        else:
            os.environ["GIT_INDEX_FILE"] = previous


def outputs_of(module: object) -> tuple[Path, ...]:
    """The tracked files a closed-phase builder writes."""
    outputs = getattr(module, "OUTPUTS", None) or (module.OUT,)
    return tuple(Path(p) for p in outputs)


def replay(
    root: Path, tasks: tuple[str, ...] = tuple(CLOSED_PHASE_BUILDERS)
) -> list[str]:
    """Rebuild each closed phase in its snapshot and require the committed bytes.

    Nothing in the repository is written: every builder writes into its own
    temporary view, and its outputs are compared with the committed files.
    """
    import importlib

    root = root.resolve()
    report = []
    for task in tasks:
        module = importlib.import_module(CLOSED_PHASE_BUILDERS[task])
        carved = outputs_of(module)
        with closure_view(root, carved) as (view, env), git_index(env):
            module.build(view)
            for relative in carved:
                if (view / relative).read_bytes() != (root / relative).read_bytes():
                    raise AssertionError(f"{task}: {relative} does not reproduce")
        report.append(f"{task}: {len(carved)} output(s) reproduced byte for byte")
    return report


if __name__ == "__main__":  # pragma: no cover
    from dt_adoc.model.provenance import repo_root

    for line in replay(
        repo_root(), tuple(sys.argv[1:]) or tuple(CLOSED_PHASE_BUILDERS)
    ):
        print(line)
