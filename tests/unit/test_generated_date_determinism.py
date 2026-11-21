"""Regenerating a tracked document must not depend on the calendar.

Five committed reports used to end their generated-file banner with
`Generated <today>`. Nothing scientific read that date, but it made the build
non-idempotent: running `pixi run build-stage3-design` on a later day rewrote a
tracked file with identical content and a new stamp, so a clean checkout went
dirty for no reason, and a real content change could hide inside a diff that
looked like the usual date churn.

The guard is deliberately not "the banner contains no date". That sentence can
be true while the generator still reads the clock somewhere else. Instead every
generator is executed twice, in two subprocesses whose system clock and time
zone differ by decades, and every file it writes is compared byte for byte --
against the other run, and against what is committed. A generator that reads
the clock at all fails here, whatever it does with the value.

Nothing is written into the checked-out tree. Each run builds into a shadow
root whose inputs are symlinks to this repository and whose output directories
are real and empty, so an interrupted or concurrent run cannot leave the working
tree holding half-regenerated artifacts -- this repository is worked on from
more than one checkout. The isolation is asserted rather than assumed: a
symlinked output would be written *through*, back into the tracked file, which
would also make the committed-versus-produced comparison vacuous, so the test
checks that no output exists in the shadow before a run and that every tracked
output is byte- and mtime-unchanged after all of them.

`ClockFrozenRegenerationTest` is the run-twice guard. `BannerTest` is the cheap
static backstop for a date arriving by a route a frozen clock cannot intercept,
such as a subprocess or a file timestamp.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc import closure_replay
from dt_adoc.experiments import (
    calibration_candidates,
    phase1b_closure,
    stage3_design,
    u8_stage3_rerank,
    variant_discrimination,
)
from dt_adoc.personalization import phase2a_contract
from dt_adoc.personalization.phase2b import audit as phase2b_audit
from dt_adoc.reporting import target_levels

#: An ISO date anywhere in the generated-file banner.
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


@dataclass(frozen=True)
class Generator:
    """One `pixi run build-*` task and every tracked file it writes."""

    module: str
    task: str
    outputs: tuple[Path, ...]


GENERATORS = (
    Generator(
        module=target_levels.__name__,
        task="build-target-level-rederivation",
        outputs=(target_levels.OUT_MD, target_levels.OUT_TSV),
    ),
    Generator(
        module=variant_discrimination.__name__,
        task="build-variant-discrimination",
        outputs=(variant_discrimination.OUT_MD, variant_discrimination.OUT_TSV),
    ),
    Generator(
        module=stage3_design.__name__,
        task="build-stage3-design",
        outputs=(
            stage3_design.OUT_MD,
            stage3_design.OUT_TSV,
            stage3_design.OUT_TABLES,
        ),
    ),
    Generator(
        module=u8_stage3_rerank.__name__,
        task="build-u8-stage3-rerank",
        outputs=u8_stage3_rerank.OUTPUTS,
    ),
    Generator(
        module=phase1b_closure.__name__,
        task="build-phase1b-closure",
        outputs=phase1b_closure.OUTPUTS,
    ),
    Generator(
        module=phase2a_contract.__name__,
        task="build-phase2a-contract",
        outputs=phase2a_contract.OUTPUTS,
    ),
    Generator(
        module=phase2b_audit.__name__,
        task="build-phase2b-audit",
        outputs=(phase2b_audit.OUT,),
    ),
    Generator(
        module=calibration_candidates.__name__,
        task="build-calibration-candidates",
        outputs=(calibration_candidates.OUT_MD, calibration_candidates.OUT_TSV),
    ),
)

#: Two wall clocks far enough apart that any date, year or epoch second a
#: generator might embed differs between the runs. The zones differ too, so a
#: naive local-time format is caught as well as a UTC one.
CLOCKS = (
    ("2001-02-03T04:05:06", "UTC"),
    ("2099-12-31T23:30:00", "Pacific/Kiritimati"),
)

#: Freezes the clock *before* the generator is imported, so a module-level
#: `from datetime import datetime` binds the frozen class rather than the real
#: one. `time.time` is redirected too, because an epoch second formatted later
#: is the same defect wearing a different import.
RUNNER = """
import datetime, time

_frozen = datetime.datetime.fromisoformat({moment!r}).replace(
    tzinfo=datetime.timezone.utc
)


class _FrozenDatetime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        return _frozen.astimezone(tz) if tz else _frozen.replace(tzinfo=None)

    @classmethod
    def utcnow(cls):
        return _frozen.replace(tzinfo=None)

    @classmethod
    def today(cls):
        return _frozen.replace(tzinfo=None)


datetime.datetime = _FrozenDatetime
_real_localtime, _real_gmtime = time.localtime, time.gmtime
time.time = lambda: _frozen.timestamp()
time.localtime = lambda secs=None: _real_localtime(
    _frozen.timestamp() if secs is None else secs
)
time.gmtime = lambda secs=None: _real_gmtime(
    _frozen.timestamp() if secs is None else secs
)

import importlib
from pathlib import Path

importlib.import_module({module!r}).build(Path({root!r}))
"""


def _mirror(source: Path, destination: Path, carved: tuple[Path, ...]) -> None:
    """Symlink every input; make a real, empty place for every output.

    A carved path is left absent rather than symlinked: `write_text` follows a
    symlink and truncates its target, so symlinking an output would write the
    tracked file itself -- the opposite of the isolation this buys.

    Cheap regardless of repository size: only the directories on the way to an
    output are created, and `data/` and `models/` are single symlinks.
    """
    destination.mkdir(parents=True, exist_ok=True)
    for entry in source.iterdir():
        relative = entry.relative_to(ROOT)
        if relative in carved:
            continue
        holds_an_output = entry.is_dir() and any(
            path.is_relative_to(relative) for path in carved
        )
        if holds_an_output:
            _mirror(entry, destination / entry.name, carved)
        else:
            (destination / entry.name).symlink_to(entry)


def _shadow_root(parent: Path, generator: Generator) -> Path:
    root = parent / "shadow"
    _mirror(ROOT, root, generator.outputs)
    return root


def _regenerate(
    generator: Generator,
    moment: str,
    zone: str,
    root: Path,
    extra_env: dict[str, str] | None = None,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            RUNNER.format(moment=moment, module=generator.module, root=str(root)),
        ],
        cwd=root,
        env={
            "PATH": "/usr/bin:/bin",
            "PYTHONPATH": str(SRC),
            "PYTHONDONTWRITEBYTECODE": "1",
            "TZ": zone,
            **(extra_env or {}),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"{generator.module} failed under a frozen clock:\n{result.stderr}"
        )


def _written(generator: Generator, root: Path) -> dict[Path, bytes]:
    return {relative: (root / relative).read_bytes() for relative in generator.outputs}


def _stamp(path: Path) -> tuple[bytes, int]:
    """Content and last-write time, so a rewrite with identical bytes shows up."""
    return path.read_bytes(), path.stat().st_mtime_ns


from tests.unit.source_history import missing
from tests.unit.source_history import reason as history_reason


class ClockFrozenRegenerationTest(unittest.TestCase):
    """Two runs, a century apart, must write the same bytes."""

    def test_regeneration_is_byte_identical_across_wall_clock_dates(self) -> None:
        tracked = {
            relative: _stamp(ROOT / relative)
            for generator in GENERATORS
            for relative in generator.outputs
        }
        for generator in GENERATORS:
            with self.subTest(task=generator.task):
                if generator.task in closure_replay.CLOSED_PHASE_BUILDERS:
                    # The closed-phase replay view is built from a frozen commit
                    # of the DT-ADOC history (tests/unit/source_history.py).
                    absent = missing(closure_replay.PHASE2B_CLOSURE_COMMIT)
                    if absent:
                        self.skipTest(history_reason(*absent))
                produced = []
                for moment, zone in CLOCKS:
                    with tempfile.TemporaryDirectory() as tmp:
                        extra_env: dict[str, str] = {}
                        if generator.task in closure_replay.CLOSED_PHASE_BUILDERS:
                            # A closed phase is reproduced against its frozen
                            # closure-time models/ (src/dt_adoc/closure_replay.py).
                            root, index = closure_replay.build_view(
                                ROOT, Path(tmp), generator.outputs
                            )
                            extra_env = {"GIT_INDEX_FILE": str(index)}
                        else:
                            root = _shadow_root(Path(tmp), generator)
                        for relative in generator.outputs:
                            self.assertFalse(
                                os.path.lexists(root / relative),
                                f"{relative} exists in the shadow root before "
                                "the run; if it is a symlink the generator "
                                "writes through it into the checked-out tree",
                            )
                        _regenerate(generator, moment, zone, root, extra_env)
                        produced.append(_written(generator, root))
                first, second = produced
                for relative in generator.outputs:
                    self.assertEqual(
                        first[relative],
                        second[relative],
                        f"{relative} changed between {CLOCKS[0][0]} and "
                        f"{CLOCKS[1][0]}: `pixi run {generator.task}` reads the "
                        "wall clock",
                    )
                    self.assertEqual(
                        (ROOT / relative).read_bytes(),
                        first[relative],
                        f"{relative} is not what `pixi run {generator.task}` "
                        "produces from the committed inputs; regenerate and "
                        "commit it",
                    )
        for relative, stamp in tracked.items():
            self.assertEqual(
                stamp,
                _stamp(ROOT / relative),
                f"{relative} was written during the test; the shadow root is "
                "not isolating the runs, which also makes the comparison "
                "against the committed bytes vacuous",
            )


class BannerTest(unittest.TestCase):
    """The generated-file banner names the generator, not the day."""

    @staticmethod
    def _banner(relative: Path) -> str:
        return next(
            line
            for line in (ROOT / relative).read_text(encoding="utf-8").splitlines()
            if "Generated file — do not edit" in line
        )

    def test_no_banner_carries_a_generation_date(self) -> None:
        for generator in GENERATORS:
            for relative in generator.outputs:
                if relative.suffix != ".md":
                    continue
                with self.subTest(document=str(relative)):
                    self.assertIsNone(
                        ISO_DATE.search(self._banner(relative)),
                        f"{relative} stamps a generation date into its banner; "
                        "a wall-clock date no scientific claim reads is not "
                        "recorded in a tracked artifact",
                    )

    def test_the_banner_still_records_the_model_it_was_derived_from(self) -> None:
        """Dropping the date must not drop real provenance with it."""
        for relative in (
            variant_discrimination.OUT_MD,
            stage3_design.OUT_MD,
            calibration_candidates.OUT_MD,
            target_levels.OUT_MD,
        ):
            with self.subTest(document=str(relative)):
                self.assertIn(
                    variant_discrimination.MODEL_VERSION, self._banner(relative)
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
