"""A sandbox repository for the O8 gates.

``build_sandbox`` copies what a run reads (``models/``, ``config/``, the evidence
register, the Stage 4b expressivity artefacts and the §3.5.1 floor table) plus
this fixture directory into a temporary root, then appends the named compounds'
rows to the sandbox copies of the evidence register, the target declarations,
the effect-adjudication ledger and the library. The production runner is then
pointed at that root, unpatched.

Appending library rows changes the arms of the expressivity artefact (one per
veto-mode library intervention), so ``add_compound`` regenerates the two
``docs/stage4b`` tables with the committed generator, exactly as
``pixi run veto-expressivity write`` would. That is the only file it rewrites;
the four compound files are only appended to.

Copies rather than symlinks, because ``describe_file`` resolves a path and
records it relative to the root, which a symlink out of the root would break.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from dt_adoc.perturbations.adjudication import (
    DECLARATIONS_PATH,
    EXPRESSIVITY_ARTEFACTS,
    FLOOR_CANDIDATES_PATH,
)
from dt_adoc.reporting import veto_expressivity

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = Path(__file__).resolve().parent
FIXTURE_RELATIVE = FIXTURE.relative_to(ROOT)
MODEL_VERSION = "adoc-literature-superset-v0.6.0"
LIBRARY = Path("config/intervention_library.tsv")
REGISTER = Path("context/evidence-register.tsv")
ADJUDICATIONS = Path("config/direct_effect_adjudications.tsv")
DECLARATIONS = DECLARATIONS_PATH
#: Each part of a compound's data and the file it is appended to, in the order
#: an admission adds them. After Stage 4b a production direct row needs all four
#: (docs/stage4b_direct_admission.md §7).
PARTS = {
    "evidence": REGISTER,
    "declaration": DECLARATIONS,
    "adjudication": ADJUDICATIONS,
    "library": LIBRARY,
}
#: The only paths in a sandbox that adding a compound may append to.
COMPOUND_DATA = (LIBRARY, REGISTER, DECLARATIONS, ADJUDICATIONS)
#: The generated tables adding a compound regenerates, and nothing else.
GENERATED = tuple(path for paths in EXPRESSIVITY_ARTEFACTS.values() for path in paths)


def build_sandbox(destination: Path, compounds: tuple[str, ...] = ()) -> Path:
    """A root that runs as the repository does, with ``compounds`` added."""
    shutil.copytree(ROOT / "models", destination / "models")
    shutil.copytree(ROOT / "config", destination / "config")
    for path in (REGISTER, FLOOR_CANDIDATES_PATH, *GENERATED):
        (destination / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, destination / path)
    shutil.copytree(
        FIXTURE,
        destination / FIXTURE_RELATIVE,
        ignore=shutil.ignore_patterns("__pycache__", "*.py"),
    )
    for compound in compounds:
        add_compound(destination, compound)
    return destination


def add_compound(
    root: Path, compound: str, parts: tuple[str, ...] = tuple(PARTS)
) -> None:
    """Add ``compound`` to a sandbox: append its rows, and nothing else.

    ``parts`` selects which of its files to append, so a test can add the
    evidence, the declaration, the approval and the library rows one at a time.
    Appending library rows regenerates the expressivity artefacts.
    """
    for part in parts:
        rows = (FIXTURE / f"{compound}.{part}.tsv").read_text(encoding="utf-8")
        with (root / PARTS[part]).open("a", encoding="utf-8") as handle:
            handle.write(rows)
    if "library" in parts:
        regenerate_expressivity(root)


def regenerate_expressivity(root: Path) -> None:
    """Rewrite the sandbox's expressivity artefacts with the committed generator."""
    (root / veto_expressivity.OUTPUT_PATH).write_text(
        veto_expressivity.render(veto_expressivity.expressivity(root=root)),
        encoding="utf-8",
    )
    (root / veto_expressivity.INVARIANCE_PATH).write_text(
        veto_expressivity.render_invariance(veto_expressivity.invariance(root=root)),
        encoding="utf-8",
    )


def tree_digest(root: Path) -> dict[str, str]:
    """``{relative path: sha256}`` for every file under ``root``."""
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
