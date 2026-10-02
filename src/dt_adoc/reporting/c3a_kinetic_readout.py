"""C3a: kinetic readouts of the current hard perturbations on v0.5.2.

Implements the governing C3a specification:
``docs/c3_kinetic_readouts/preregistration.md`` as committed at
``PREREG_COMMIT``, plus ``preregistration_addendum_01.md`` as committed at
``ADDENDUM_COMMIT``. The addendum governs where they differ: anti-SPP1 and the
washout arms are out of scope, and each family has 4 bands. The constants
below are typed in from those files, not read from them at run time.
``tests/unit/test_c3a_kinetic_readout.py`` checks them against their text. If a
constant here and the files ever disagree, the files are right and this module
is the defect.

What it does, in pre-registration order:

* runs the phase plan of section 3 per seed block: the shared prefix, the
  schedule-matching HT extension, the maternal perturbation phases, and every
  challenge at the declared horizon and at the converged horizon;
* the converged run extends **only the challenge phase** to
  ``CONVERGED_PHASE_HORIZON``. Every pre-challenge phase keeps its declared
  duration. Section 4 forbids ``run_arm(horizon_class="converged")``, which sets
  every phase to 25, and this module never calls it;
* computes the section 6 estimands, the section 7 empirical paired-block
  reproducibility bands, the section 9 classes and the section 10
  trajectory-count sensitivity check;
* writes the descriptive outputs of section 11.

No seed is spent unless ``build`` is called with ``execute=True``. Before any
seed is spent:

* ``bind_inputs`` refuses if any bound input differs from its blob at
  ``PREREG_COMMIT``, or if a bound input or any file under ``src/dt_adoc/``
  (``execution_dependencies``) is modified or untracked;
* ``check_construction`` refuses if the section 3 pairs are not matched;
* ``reserve_attempt`` refuses if any planned seed was reserved by an earlier
  attempt, then journals this attempt under ``docs/c3_kinetic_readouts/attempts/``.

Every dispatched task counts as spent. On any exception, from a worker, the
end-of-run hash check, the comparison or the writers, the journal records
``FAILED`` with the error and the spent seed ranges, and the exception is
re-raised. A rerun needs a dated addendum with fresh, disjoint seeds. A new
reservation is also refused whenever canonical outputs already exist.

The manifest and the journal are one provenance object, validated by
rebuilding rather than by an allow-list (``manifest_problems``):

* the schema is closed (``MANIFEST_FIELDS``);
* ``RECONSTRUCTED_FIELDS`` are rebuilt from the frozen constants, the protocols
  and the outputs, and must match exactly;
* the outputs must be one derivation, with bands and classes re-derived from
  ``blocks.tsv`` and ``curves.tsv``;
* each ``RUN_VARYING_FIELDS`` entry has its own rule. The binding resolves
  through git, with inputs re-hashed from the ``start_head`` blobs, and the
  journal named by ``attempt_id`` must agree field by field.

States run RESERVED, DISPATCHED, SIMULATED, FINALIZING, then COMPLETED, which
is written only after validation accepts the FINALIZING state.

Time is dimensionless MaBoSS relative time throughout. No rate, horizon,
crossing threshold or physical-time mapping is introduced.
"""

from __future__ import annotations

import functools
import hashlib
import json
import math
import platform
import subprocess
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from statistics import mean, stdev
from typing import Any

from dt_adoc.model.provenance import repo_root

MODEL_VERSION = "adoc-literature-superset-v0.5.2"
MODEL_DIR = Path("models/superset") / MODEL_VERSION
PREREGISTRATION = Path("docs/c3_kinetic_readouts/preregistration.md")
#: The reviewed, merged head that froze the pre-registration.
PREREG_COMMIT = "0c7da9c174b69a58b97292572684f86e2cbdb185"
#: Addendum 01 (anti-SPP1 out of scope, 4 bands per family), committed alone.
ADDENDUM = Path("docs/c3_kinetic_readouts/preregistration_addendum_01.md")
ADDENDUM_COMMIT = "ef34c1079267650f1359635d3b8b60ce48518546"
#: The governing specification, as the manifest and journal name it.
GOVERNING_SPECIFICATION = [str(PREREGISTRATION), str(ADDENDUM)]

OUTPUT_DIR = Path("docs/c3_kinetic_readouts")
CLASSES_TSV = OUTPUT_DIR / "classification.tsv"
BANDS_TSV = OUTPUT_DIR / "bands.tsv"
BLOCKS_TSV = OUTPUT_DIR / "blocks.tsv"
CURVES_TSV = OUTPUT_DIR / "curves.tsv"
SETTINGS_JSON = OUTPUT_DIR / "run_settings.json"

# Section 2.
PRIMARY_READOUT = "OUT_STABLE_ADHESION"
SECONDARY_READOUT = "OUT_MATERNAL_ADHESION_COMPETENCE"
READOUTS = (PRIMARY_READOUT, SECONDARY_READOUT)
FAMILY_OF = {PRIMARY_READOUT: "primary", SECONDARY_READOUT: "secondary"}

# Section 4.
CONVERGED_PHASE_HORIZON = 25.0

# Section 5.
REPLICATES = 20
GOVERNING_TRAJECTORIES = 20_000
CHECK_TRAJECTORIES = 2_000
TRAJECTORY_COUNTS = (GOVERNING_TRAJECTORIES, CHECK_TRAJECTORIES)

# Sections 6-10.
SNAP = 1e-12
DELTA = 0.005
INTERVALS_PER_FAMILY = 4  # addendum 01: 2 pairs x 2 estimands
FAMILY_ALPHA = 0.05
T19 = 2.758586  # addendum 01, two-sided at 0.05 / 4
Q = 2.497705  # addendum 01, two-sided at 0.05 / 4
ESTIMANDS = ("finite_window_occupancy", "fixed_point")

# Section 9 labels and classes.
SUPPRESSED = "materially_suppressed"
EQUIVALENT = "equivalent"
INCREASED = "material_increase"
NEITHER = "neither"
PERSISTENT = "PERSISTENT_SUPPRESSION"
TRANSIENT = "TRANSIENT_SUPPRESSION_CONSISTENT_WITH_DELAY"
NO_DIFFERENCE = "NO_MATERIAL_DIFFERENCE_DETECTED"
INDETERMINATE = "INDETERMINATE"
COUNT_SENSITIVE_CLASS = "trajectory_count_sensitive"
ZERO_OCCUPANCY = "NO_ON_OCCUPANCY_OBSERVED_AT_RECORDED_TICKS"
SOME_OCCUPANCY = "ON_OCCUPANCY_OBSERVED_AT_SOME_RECORDED_TICK"

# Section 10 records.
STABLE = "STABLE"
LOW_COUNT = "LOW_COUNT_LABEL_DIFFERENCE"
COUNT_SENSITIVE = "TRAJECTORY_COUNT_SENSITIVE"

CLAIM_BOUNDARY = (
    "Paired differences of MaBoSS readout occupancy on adoc-literature-superset-"
    "v0.5.2 under default (unit) rates, in dimensionless relative time, between "
    "a perturbed lineage and its schedule-matched unperturbed twin. Bands are "
    "empirical paired-block reproducibility bands across 20 disjoint seed "
    "blocks: no confidence-interval coverage or family-wise error control is "
    "claimed. PERSISTENT_SUPPRESSION is never a literal block, and "
    "NO_ON_OCCUPANCY_OBSERVED_AT_RECORDED_TICKS licenses no statement of "
    "unreachability. No biological, clinical, kinetic or physical-time claim; no "
    "rate value; the HT extension is a model counterfactual, not an ADOC condition."
)


def replicate_seed(replicate: int, trajectory_count: int) -> int:
    """Section 5: fresh blocks, disjoint from every range used before."""
    if not 0 <= replicate < REPLICATES:
        raise ValueError(f"replicate {replicate} is not pre-registered")
    if trajectory_count == GOVERNING_TRAJECTORIES:
        return 2_000_001 + replicate * GOVERNING_TRAJECTORIES
    if trajectory_count == CHECK_TRAJECTORIES:
        return 2_400_001 + replicate * CHECK_TRAJECTORIES
    raise ValueError(f"trajectory count {trajectory_count} is not pre-registered")


# ---------------------------------------------------------------------------
# Section 3: the phase plan.


@dataclass(frozen=True)
class Phase:
    """One MaBoSS task: one protocol phase, continued from ``parent``."""

    key: str
    protocol_id: str
    parent: str | None
    horizon: str  # "declared" or "converged"
    duration_from: str | None = None  # protocol whose declared duration is used


#: Challenge arms: key -> (challenge protocol, parent phase key).
CHALLENGES: dict[str, tuple[str, str]] = {
    "twin": ("adhesion_challenge_hormone_treated", "ht"),
    "control_ext": ("adhesion_challenge_hormone_treated", "ht_extension"),
    "mifepristone": (
        "adhesion_challenge_hormone_treated_mifepristone",
        "mifepristone_maternal",
    ),
    "hand2_loss": (
        "adhesion_challenge_hormone_treated_hand2_loss",
        "hand2_loss_maternal",
    ),
}

#: Classified pairs: pair -> (control arm, perturbed arm, the differing input).
PAIRS: dict[str, tuple[str, str, str]] = {
    "mifepristone": ("control_ext", "mifepristone", "IN_MIFEPRISTONE"),
    "hand2_loss": ("twin", "hand2_loss", "IN_HAND2_LOSS"),
}

#: Section 11: declared-but-unmatched contrasts, never classified.
UNMATCHED: dict[str, tuple[str, str]] = {
    "mifepristone_vs_declared_twin": ("twin", "mifepristone"),
}


def phase_plan() -> tuple[Phase, ...]:
    """Every MaBoSS task of one governing block, parents before children."""
    phases = [
        Phase("basal", "basal_maternal", None, "declared"),
        Phase("e2", "e2_primed_maternal", "basal", "declared"),
        Phase("ht", "hormone_treated_maternal", "e2", "declared"),
        # The schedule-matching counterfactual: HT inputs, run for exactly the
        # perturbation phase's declared duration (section 3; addendum 01 reads
        # it from the mifepristone phase).
        Phase(
            "ht_extension",
            "hormone_treated_maternal",
            "ht",
            "declared",
            duration_from="hormone_treated_mifepristone",
        ),
        Phase(
            "mifepristone_maternal", "hormone_treated_mifepristone", "ht", "declared"
        ),
        Phase("hand2_loss_maternal", "hormone_treated_hand2_loss", "e2", "declared"),
    ]
    for arm, (protocol_id, parent) in CHALLENGES.items():
        phases.append(Phase(f"{arm}@declared", protocol_id, parent, "declared"))
        phases.append(Phase(f"{arm}@converged", protocol_id, parent, "converged"))
    return tuple(phases)


def plan_for(trajectory_count: int) -> tuple[Phase, ...]:
    """Addendum 01: the same 14 tasks per block at both trajectory counts."""
    if trajectory_count not in TRAJECTORY_COUNTS:
        raise ValueError(f"trajectory count {trajectory_count} is not pre-registered")
    return phase_plan()


def _protocol(root: Path, protocol_id: str) -> Any:
    from dt_adoc.protocols.conditions import get_protocol

    return get_protocol(protocol_id, root, model_version=MODEL_VERSION)


def phase_duration(root: Path, phase: Phase) -> float:
    """The relative duration a phase runs for; never typed in."""
    if phase.horizon == "converged":
        return CONVERGED_PHASE_HORIZON
    source = _protocol(root, phase.duration_from or phase.protocol_id)
    (step,) = source.steps
    return float(step.relative_duration)


def _chain(key: str) -> list[Phase]:
    """The phases from the first to ``key``, following parents."""
    by_key = {p.key: p for p in phase_plan()}
    chain = [by_key[key]]
    while chain[-1].parent is not None:
        chain.append(by_key[chain[-1].parent])
    return list(reversed(chain))


def _lineage(arm: str) -> list[Phase]:
    return _chain(f"{arm}@declared")


def _describe(root: Path, phase: Phase) -> dict[str, Any]:
    protocol = _protocol(root, phase.protocol_id)
    (step,) = protocol.steps
    continuation = protocol.continuation
    return {
        "protocol_id": phase.protocol_id,
        "duration": phase_duration(root, phase),
        "inputs": dict(step.input_states),
        "continuation": None
        if continuation is None
        else [
            continuation.mode,
            continuation.memory_policy,
            continuation.probability_cutoff,
        ],
        "condition_cfg": protocol.condition_cfg,
    }


def _changed_cfg_lines(left: Path, right: Path) -> tuple[list[str], list[str]]:
    """Lines only in ``left`` and lines only in ``right``, by a line diff."""
    import difflib

    a = left.read_text(encoding="utf-8").splitlines()
    b = right.read_text(encoding="utf-8").splitlines()
    diff = list(difflib.unified_diff(a, b, lineterm="", n=0))[2:]
    removed = [line[1:] for line in diff if line.startswith("-")]
    added = [line[1:] for line in diff if line.startswith("+")]
    return removed, added


def check_construction(root: Path | None = None) -> dict[str, Any]:
    """Section 3's verification, re-run before any seed is spent.

    Raises ``ValueError`` on the first violation.
    """
    from dt_adoc.concordance.simulate import protocol_lineage

    root = root or repo_root()
    record: dict[str, Any] = {}
    for arm, (protocol_id, _) in CHALLENGES.items():
        if arm == "control_ext":
            continue
        declared = list(
            protocol_lineage(protocol_id, model_version=MODEL_VERSION, root=root)
        )
        planned = [p.protocol_id for p in _lineage(arm)]
        if planned != declared:
            raise ValueError(
                f"{arm}: planned lineage {planned} is not the declared {declared}"
            )
    # The HT extension equals the mifepristone phase's declared duration by
    # construction (Phase.duration_from); there is nothing further to check here.
    # tests/unit/test_c3a_kinetic_readout.py pins that run_block passes 2.0.
    for pair, (control, perturbed, input_id) in PAIRS.items():
        left = [_describe(root, p) for p in _lineage(control)]
        right = [_describe(root, p) for p in _lineage(perturbed)]
        if len(left) != len(right):
            raise ValueError(f"{pair}: phase counts differ")
        differing = []
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            if a["duration"] != b["duration"]:
                raise ValueError(f"{pair}: phase {index} durations differ")
            if a["continuation"] != b["continuation"]:
                raise ValueError(f"{pair}: phase {index} continuation rules differ")
            keys = set(a["inputs"]) | set(b["inputs"])
            diff = {
                k
                for k in keys
                if a["inputs"].get(k, False) != b["inputs"].get(k, False)
            }
            if diff and diff != {input_id}:
                raise ValueError(
                    f"{pair}: phase {index} inputs differ in {sorted(diff)}"
                )
            changed = _changed_cfg_lines(
                root / a["condition_cfg"], root / b["condition_cfg"]
            )
            if diff:
                differing.append(index)
                removed, added = changed
                if (
                    len(added) != 1
                    or len(removed) > 1
                    or not all(input_id in line for line in (*removed, *added))
                ):
                    raise ValueError(
                        f"{pair}: phase {index} condition files differ beyond {input_id}"
                    )
            elif any(changed):
                raise ValueError(
                    f"{pair}: phase {index} condition files differ with equal inputs"
                )
        expected = list(range(len(left) - 2, len(left)))
        if differing != expected:
            raise ValueError(
                f"{pair}: {input_id} differs in phases {differing}, expected {expected}"
            )
        record[pair] = {
            "control": [d["protocol_id"] for d in left],
            "perturbed": [d["protocol_id"] for d in right],
            "durations": [d["duration"] for d in left],
            "differing_phases": differing,
            "differing_input": input_id,
        }
    return record


# ---------------------------------------------------------------------------
# Section 12: binding the run to the pre-registered state.

#: Scientific inputs whose bytes must equal their frozen blob: the addendum at
#: ADDENDUM_COMMIT, everything else at PREREG_COMMIT (``frozen_commit``).
BOUND_PATHS = (
    str(PREREGISTRATION),
    str(ADDENDUM),
    "config/protocols.yaml",
    "models/specs/parameter_scenarios.yaml",
)
#: The generator inventory: every Python file of the package. Deliberately
#: conservative and defined only by the source it is read from, so that
#: reconstructing it at an old commit uses nothing from the current checkout.
GENERATOR_PACKAGE = "src/dt_adoc/"


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class _Source:
    """Repository files read either from the working tree or from one git commit."""

    def __init__(self, root: Path, commit: str | None = None) -> None:
        self.root = root
        # Resolve refs such as HEAD to an immutable object id, so cached reads
        # can never serve another commit's bytes.
        self.commit = (
            None
            if commit is None
            else _git(root, "rev-parse", "--verify", f"{commit}^{{commit}}").strip()
        )
        self._listing: set[str] | None = None

    def files(self) -> set[str]:
        if self._listing is None:
            if self.commit is None:
                self._listing = set(_git(self.root, "ls-files").split("\n")) - {""}
            else:
                self._listing = set(
                    _git(self.root, "ls-tree", "-r", "--name-only", self.commit).split(
                        "\n"
                    )
                ) - {""}
        return self._listing

    def is_file(self, path: str) -> bool:
        if self.commit is None:
            return (self.root / path).is_file()
        return path in self.files()

    def read(self, path: str) -> bytes:
        if self.commit is None:
            return (self.root / path).read_bytes()
        return _blob(str(self.root), self.commit, path)


@functools.lru_cache(maxsize=4096)
def _blob(root: str, commit: str, path: str) -> bytes:
    """A file at a commit. Commits are immutable, so the read can be cached."""
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=root, check=True, capture_output=True
    ).stdout


def execution_dependencies(root: Path, commit: str | None = None) -> tuple[str, ...]:
    """Every tracked ``src/dt_adoc/**/*.py``, from the working tree or ``commit``.

    A superset of anything the run can import. It is read entirely from the
    source it describes: at ``commit`` it is that commit's file listing, and no
    definition from the current checkout (import graph, glob patterns) takes
    part. Untracked package files are refused at bind time instead
    (``bind_inputs``).
    """
    source = _Source(root, commit)
    return tuple(
        sorted(
            f
            for f in source.files()
            if f.startswith(GENERATOR_PACKAGE) and f.endswith(".py")
        )
    )


def frozen_commit(path: str) -> str:
    """The commit whose blob a bound path must equal."""
    return ADDENDUM_COMMIT if path == str(ADDENDUM) else PREREG_COMMIT


def bound_paths(root: Path) -> list[str]:
    """BOUND_PATHS plus every file of the v0.5.2 model tree at PREREG_COMMIT."""
    tree = _git(
        root, "ls-tree", "-r", "--name-only", PREREG_COMMIT, "--", str(MODEL_DIR)
    )
    return sorted(set(BOUND_PATHS) | set(tree.split()))


def input_hashes(root: Path, commit: str | None = None) -> dict[str, dict[str, str]]:
    """Bound and generator sha256s, from the working tree or from ``commit``."""
    source = _Source(root, commit)
    return {
        "bound": {p: _sha(source.read(p)) for p in bound_paths(root)},
        "generator": {
            p: _sha(source.read(p)) for p in execution_dependencies(root, commit)
        },
    }


def bind_inputs(root: Path | None = None) -> dict[str, Any]:
    """Refuse unless the run is bound to the pre-registered, committed state."""
    root = root or repo_root()
    problems = []
    for path in bound_paths(root):
        frozen = subprocess.run(
            ["git", "show", f"{frozen_commit(path)}:{path}"],
            cwd=root,
            capture_output=True,
            check=True,
        ).stdout
        if (root / path).read_bytes() != frozen:
            problems.append(
                f"{path} differs from its blob at {frozen_commit(path)[:7]}"
            )
    model_now = _git(root, "ls-files", "--", str(MODEL_DIR)).split()
    frozen_model = [p for p in bound_paths(root) if p.startswith(str(MODEL_DIR))]
    if sorted(model_now) != frozen_model:
        problems.append(
            "the v0.5.2 model tree gained or lost files since the pre-registration"
        )
    # The package pathspec also reports untracked files, so an untracked module
    # that tracked code could import is refused too.
    dirty = _git(
        root,
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--",
        *bound_paths(root),
        GENERATOR_PACKAGE,
    )
    if dirty.strip():
        problems.append(f"uncommitted changes to bound or generator files:\n{dirty}")
    if problems:
        raise RuntimeError("C3a refuses to spend seeds: " + "; ".join(problems))
    return {
        "prereg_commit": PREREG_COMMIT,
        "addendum_commit": ADDENDUM_COMMIT,
        "start_head": _git(root, "rev-parse", "HEAD").strip(),
        "start_tree": _git(root, "rev-parse", "HEAD^{tree}").strip(),
        "start_dirty_paths": _git(root, "status", "--porcelain").splitlines(),
        "input_sha256_at_start": input_hashes(root),
    }


# ---------------------------------------------------------------------------
# Execution: one block (seed) at one trajectory count.


@dataclass(frozen=True)
class Task:
    trajectory_count: int
    replicate: int
    root: str


def run_block(task: Task) -> dict[str, Any]:
    """Every phase of ``plan_for(count)`` on one seed; the two readouts per tick."""
    import warnings

    from dt_adoc.simulation.runner import protocol_continuation, run_protocol

    root = Path(task.root)
    seed = replicate_seed(task.replicate, task.trajectory_count)
    results: dict[str, Any] = {}
    series: dict[str, dict[str, Any]] = {}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _run_phases(
            task, root, seed, results, series, protocol_continuation, run_protocol
        )
    return {
        "trajectory_count": task.trajectory_count,
        "replicate": task.replicate,
        "seed": seed,
        "series": series,
        "warnings": sorted({f"{w.category.__name__}: {w.message}" for w in caught}),
    }


def _run_phases(
    task, root, seed, results, series, protocol_continuation, run_protocol
) -> None:
    for phase in plan_for(task.trajectory_count):
        continuation = None
        if phase.parent is not None:
            continuation = protocol_continuation(
                phase.protocol_id,
                results[phase.parent],
                model_version=MODEL_VERSION,
                root=root,
            )
        # Only the converged challenges and the HT extension override the
        # declared duration; every other phase runs as declared (section 4).
        override = None
        if phase.horizon == "converged" or phase.duration_from is not None:
            override = phase_duration(root, phase)
        result = run_protocol(
            phase.protocol_id,
            model_version=MODEL_VERSION,
            root=root,
            continuation=continuation,
            seed=seed,
            sample_count=task.trajectory_count,
            phase_horizon=override,
        )
        results[phase.key] = result
        table = result.final_result.nodes_probtraj
        series[phase.key] = {
            "times": [float(t) for t in table.index],
            **{r: [float(v) for v in table[r]] for r in READOUTS},
        }


# ---------------------------------------------------------------------------
# Sections 6-10: estimands, bands, labels, classes, count sensitivity.


def _snap(d: float) -> float:
    return 0.0 if abs(d) <= SNAP else d


def _paired(
    block: dict[str, Any], control: str, perturbed: str, horizon: str, readout: str
) -> list[float]:
    a = block["series"][f"{control}@{horizon}"]
    b = block["series"][f"{perturbed}@{horizon}"]
    if a["times"] != b["times"]:
        raise ValueError(f"{control}/{perturbed}@{horizon}: tick grids differ")
    return [_snap(y - x) for x, y in zip(a[readout], b[readout], strict=True)]


def estimands(
    block: dict[str, Any], control: str, perturbed: str, readout: str
) -> dict[str, float]:
    """Section 6: O over the declared challenge, F at the converged final tick."""
    return {
        "finite_window_occupancy": mean(
            _paired(block, control, perturbed, "declared", readout)
        ),
        "fixed_point": _paired(block, control, perturbed, "converged", readout)[-1],
    }


def band(values: list[float], multiplier: float = T19) -> dict[str, float]:
    """Section 7: mean +/- multiplier * SD / sqrt(R)."""
    centre = mean(values)
    spread = stdev(values)
    se = spread / math.sqrt(len(values))
    return {
        "mean": centre,
        "sd": spread,
        "se": se,
        "low": centre - multiplier * se,
        "high": centre + multiplier * se,
    }


def label(b: dict[str, float]) -> str:
    """Section 9, for one band."""
    if b["high"] < -DELTA:
        return SUPPRESSED
    if -DELTA <= b["low"] and b["high"] <= DELTA:
        return EQUIVALENT
    if b["low"] > DELTA:
        return INCREASED
    return NEITHER


def kinetic_class(fixed_point: str, finite_window: str) -> tuple[str, list[str]]:
    """Section 9's table; the first row that matches applies."""
    if fixed_point == SUPPRESSED:
        return PERSISTENT, []
    if fixed_point == EQUIVALENT and finite_window == SUPPRESSED:
        return TRANSIENT, []
    if fixed_point == EQUIVALENT and finite_window == EQUIVALENT:
        return NO_DIFFERENCE, []
    increase = INCREASED in (fixed_point, finite_window)
    return INDETERMINATE, (["material increase"] if increase else [])


def count_record(governing: dict[str, float], check: dict[str, float]) -> str:
    """Section 10, for one estimand."""
    compatible = abs(check["mean"] - governing["mean"]) <= Q * math.sqrt(
        check["se"] ** 2 + governing["se"] ** 2
    )
    if not compatible:
        return COUNT_SENSITIVE
    return STABLE if count_label(check) == count_label(governing) else LOW_COUNT


def count_label(b: dict[str, float]) -> str:
    """Section 10 compares three labels: materially suppressed, equivalent or
    neither. A band wholly above +delta is not a label of its own (section 9
    records it only as a descriptive direction), so it counts as neither."""
    value = label(b)
    return NEITHER if value == INCREASED else value


def zero_occupancy(blocks: list[dict[str, Any]], arm: str, readout: str) -> str:
    """Section 9's sub-label, from raw per-tick values of the governing blocks."""
    if all(v == 0.0 for b in blocks for v in b["series"][f"{arm}@converged"][readout]):
        return ZERO_OCCUPANCY
    return SOME_OCCUPANCY


def _blocks_and_curves(
    results: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Stage 1: raw blocks -> the rows of blocks.tsv and curves.tsv."""
    by_count: dict[int, list[dict[str, Any]]] = {
        count: [] for count in TRAJECTORY_COUNTS
    }
    for result in sorted(
        results, key=lambda r: (r["trajectory_count"], r["replicate"])
    ):
        by_count[result["trajectory_count"]].append(result)
    for count, blocks in by_count.items():
        if [b["replicate"] for b in blocks] != list(range(REPLICATES)):
            raise ValueError(f"N = {count}: blocks are not exactly 0..{REPLICATES - 1}")
    block_rows: list[dict[str, Any]] = []
    for contrast, control, perturbed, kind, counts in _contrasts():
        for readout in READOUTS:
            for count in counts:
                for block in by_count[count]:
                    est = estimands(block, control, perturbed, readout)
                    for e in ESTIMANDS:
                        block_rows.append(
                            {
                                "contrast": contrast,
                                "kind": kind,
                                "readout": readout,
                                "trajectory_count": count,
                                "replicate": block["replicate"],
                                "seed": block["seed"],
                                "estimand": e,
                                "difference": est[e],
                            }
                        )
    governing = by_count[GOVERNING_TRAJECTORIES]
    curve_rows: list[dict[str, Any]] = []
    for phase in phase_plan():
        grids = [b["series"][phase.key]["times"] for b in governing]
        if any(g != grids[0] for g in grids):
            raise ValueError(f"{phase.key}: tick grids differ across blocks")
        for readout in READOUTS:
            columns = list(zip(*(b["series"][phase.key][readout] for b in governing)))
            for t, column in zip(grids[0], columns, strict=True):
                curve_rows.append(
                    {
                        "phase": phase.key,
                        "protocol_id": phase.protocol_id,
                        "horizon": phase.horizon,
                        "readout": readout,
                        "time": t,
                        "mean_p_on": mean(column),
                        "sd_p_on": stdev(column),
                    }
                )
    return block_rows, curve_rows


def _contrasts() -> list[tuple[str, str, str, str, tuple[int, ...]]]:
    """(contrast, control, perturbed, kind, counts), classified pairs first."""
    out = [
        (pair, control, perturbed, "classified", TRAJECTORY_COUNTS)
        for pair, (control, perturbed, _) in PAIRS.items()
    ]
    out += [
        (
            contrast,
            control,
            perturbed,
            "schedule_unmatched_descriptive",
            (GOVERNING_TRAJECTORIES,),
        )
        for contrast, (control, perturbed) in UNMATCHED.items()
    ]
    return out


def derive(
    block_rows: list[dict[str, Any]], curve_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Stage 2: the rows of bands.tsv and classification.tsv, from stage 1 alone."""
    values: dict[tuple, list[tuple[int, float]]] = {}
    for row in block_rows:
        key = (
            row["contrast"],
            row["readout"],
            row["trajectory_count"],
            row["estimand"],
        )
        values.setdefault(key, []).append((row["replicate"], row["difference"]))
    band_rows: list[dict[str, Any]] = []
    class_rows: list[dict[str, Any]] = []
    for contrast, control, perturbed, kind, counts in _contrasts():
        bands: dict[tuple[str, str, int], dict[str, float]] = {}
        for readout in READOUTS:
            for count in counts:
                for e in ESTIMANDS:
                    pairs = sorted(values[(contrast, readout, count, e)])
                    if [r for r, _ in pairs] != list(range(REPLICATES)):
                        raise ValueError(
                            f"{contrast}/{readout}/{count}/{e}: blocks incomplete"
                        )
                    b = band([v for _, v in pairs])
                    bands[(readout, e, count)] = b
                    band_rows.append(
                        {
                            "contrast": contrast,
                            "kind": kind,
                            "readout": readout,
                            "family": FAMILY_OF[readout]
                            if kind == "classified"
                            else "none",
                            "trajectory_count": count,
                            "estimand": e,
                            **b,
                            "label": label(b)
                            if kind == "classified"
                            else "not_classified",
                        }
                    )
        if kind != "classified":
            continue
        input_id = PAIRS[contrast][2]
        for readout in READOUTS:
            labels = {
                e: label(bands[(readout, e, GOVERNING_TRAJECTORIES)]) for e in ESTIMANDS
            }
            records = {
                e: count_record(
                    bands[(readout, e, GOVERNING_TRAJECTORIES)],
                    bands[(readout, e, CHECK_TRAJECTORIES)],
                )
                for e in ESTIMANDS
            }
            cls, sub = kinetic_class(
                labels["fixed_point"], labels["finite_window_occupancy"]
            )
            if COUNT_SENSITIVE in records.values():
                cls = COUNT_SENSITIVE_CLASS
            class_rows.append(
                {
                    "pair": contrast,
                    "control_arm": control,
                    "perturbed_arm": perturbed,
                    "differing_input": input_id,
                    "readout": readout,
                    "family": FAMILY_OF[readout],
                    "fixed_point_label": labels["fixed_point"],
                    "finite_window_label": labels["finite_window_occupancy"],
                    "class": cls,
                    "sub_labels": ";".join(
                        [
                            *sub,
                            _zero_occupancy_from_curves(curve_rows, perturbed, readout),
                        ]
                    ),
                    "fixed_point_count_record": records["fixed_point"],
                    "finite_window_count_record": records["finite_window_occupancy"],
                }
            )
    return band_rows, class_rows


def _zero_occupancy_from_curves(
    curve_rows: list[dict[str, Any]], arm: str, readout: str
) -> str:
    """Section 9's sub-label. P(ON) >= 0, so the across-block mean at a tick is
    exactly 0 only if every governing block is exactly 0 at that tick."""
    means = [
        r["mean_p_on"]
        for r in curve_rows
        if r["phase"] == f"{arm}@converged" and r["readout"] == readout
    ]
    if not means:
        raise ValueError(f"no converged curve for {arm}/{readout}")
    return ZERO_OCCUPANCY if all(m == 0.0 for m in means) else SOME_OCCUPANCY


def compare(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify every pre-registered pair and assemble the descriptive outputs."""
    block_rows, curve_rows = _blocks_and_curves(results)
    band_rows, class_rows = derive(block_rows, curve_rows)
    return {
        "classes": class_rows,
        "bands": band_rows,
        "blocks": block_rows,
        "curves": curve_rows,
    }


def _tsv_text(rows: list[dict[str, Any]]) -> str:
    import csv
    import io

    handle = io.StringIO()
    writer = csv.DictWriter(
        handle, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {k: (repr(v) if isinstance(v, float) else v) for k, v in row.items()}
        )
    return handle.getvalue()


def _write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_tsv_text(rows), encoding="utf-8", newline="")


BLOCK_COLUMNS = (
    "contrast",
    "kind",
    "readout",
    "trajectory_count",
    "replicate",
    "seed",
    "estimand",
    "difference",
)
CURVE_COLUMNS = (
    "phase",
    "protocol_id",
    "horizon",
    "readout",
    "time",
    "mean_p_on",
    "sd_p_on",
)
BLOCK_TYPES = {
    "trajectory_count": int,
    "replicate": int,
    "seed": int,
    "difference": float,
}
CURVE_TYPES = {"time": float, "mean_p_on": float, "sd_p_on": float}
#: Float tolerance for tick spacing only; never applied to any estimand.
TICK_TOLERANCE = 1e-9


def _header(path: Path) -> tuple[str, ...]:
    with path.open(encoding="utf-8", newline="") as handle:
        return tuple(handle.readline().rstrip("\n").split("\t"))


def _read_typed(path: Path, types: dict[str, type]) -> list[dict[str, Any]]:
    import csv

    with path.open(encoding="utf-8", newline="") as handle:
        return [
            {k: types.get(k, str)(v) for k, v in row.items()}
            for row in csv.DictReader(handle, delimiter="\t")
        ]


def expected_block_metadata() -> list[tuple]:
    """Every blocks.tsv row except its value, in the order stage 1 writes them."""
    return [
        (contrast, kind, readout, count, r, replicate_seed(r, count), e)
        for contrast, _, _, kind, counts in _contrasts()
        for readout in READOUTS
        for count in counts
        for r in range(REPLICATES)
        for e in ESTIMANDS
    ]


def _curve_problems(curves: list[dict[str, Any]], reference_root: Path) -> list[str]:
    """curves.tsv: groups in phase_plan x readout order, metadata and time grid."""
    tick = time_settings(reference_root)["time_tick"]
    expected_groups = [
        (p.key, p.protocol_id, p.horizon, x) for p in phase_plan() for x in READOUTS
    ]
    groups: list[tuple] = []
    times: dict[tuple, list[float]] = {}
    for row in curves:
        key = (row["phase"], row["protocol_id"], row["horizon"], row["readout"])
        if not groups or groups[-1] != key:
            groups.append(key)
        times.setdefault(key, []).append(row["time"])
        mean_, sd_ = row["mean_p_on"], row["sd_p_on"]
        if not (math.isfinite(mean_) and 0.0 <= mean_ <= 1.0) or not (
            math.isfinite(sd_) and sd_ >= 0.0
        ):
            return [f"curves.tsv: {key} has a non-finite or out-of-range mean or sd"]
    if groups != expected_groups:
        return [
            (
                "curves.tsv rows are not exactly the planned phase x readout groups, in order, "
                "with their protocol and horizon"
            )
        ]
    problems = []
    durations = {p.key: phase_duration(reference_root, p) for p in phase_plan()}
    for key, grid in times.items():
        steps = [b - a for a, b in pairwise(grid)]
        duration = durations[key[0]]
        # The grid must reach the phase horizon: its last recorded time is within
        # one tick of it, which admits both the exclusive (duration - tick) and
        # the inclusive (duration) endpoint convention. A truncated prefix fails.
        if (
            not grid
            or not all(math.isfinite(t) for t in grid)
            or grid[0] != 0.0
            or any(abs(s - tick) > TICK_TOLERANCE for s in steps)
            or not (
                duration - tick - TICK_TOLERANCE
                <= grid[-1]
                <= duration + TICK_TOLERANCE
            )
        ):
            problems.append(
                f"curves.tsv: {key[0]}/{key[3]} time grid is not 0, {tick}, ... "
                f"reaching the phase horizon {duration}"
            )
    for p in phase_plan():
        a, b = (times[(p.key, p.protocol_id, p.horizon, x)] for x in READOUTS)
        if a != b:
            problems.append(f"curves.tsv: {p.key} readouts are on different time grids")
    return problems


def outputs_problems(root: Path, reference_root: Path | None = None) -> list[str]:
    """The four outputs must be one consistent derivation, with closed schemas.

    * blocks.tsv: the exact header, and every metadata column row by row equal
      to what stage 1 emits from ``_contrasts()``, including kind and seed;
    * curves.tsv: the exact header, the phase_plan x readout groups in order,
      each with its protocol and horizon, and a 0, tick, 2*tick, ... grid within
      the phase duration, shared by both readouts;
    * bands.tsv and classification.tsv: byte-identical to stage 2 re-derived
      from blocks.tsv and curves.tsv.
    """
    reference_root = reference_root or root
    problems = []
    if _header(root / BLOCKS_TSV) != BLOCK_COLUMNS:
        problems.append("blocks.tsv header is not exactly " + ", ".join(BLOCK_COLUMNS))
    if _header(root / CURVES_TSV) != CURVE_COLUMNS:
        problems.append("curves.tsv header is not exactly " + ", ".join(CURVE_COLUMNS))
    if problems:
        return problems
    blocks = _read_typed(root / BLOCKS_TSV, BLOCK_TYPES)
    curves = _read_typed(root / CURVES_TSV, CURVE_TYPES)
    metadata = [tuple(b[c] for c in BLOCK_COLUMNS[:-1]) for b in blocks]
    if metadata != expected_block_metadata():
        problems.append(
            "blocks.tsv rows are not exactly the pre-registered contrasts, kinds, "
            "readouts, blocks, seeds and estimands, in order"
        )
    # A paired difference of two probabilities lies in [-1, 1].
    if not all(
        math.isfinite(b["difference"]) and -1.0 <= b["difference"] <= 1.0
        for b in blocks
    ):
        problems.append("blocks.tsv holds a non-finite or out-of-range difference")
    problems += _curve_problems(curves, reference_root)
    if problems:
        return problems
    band_rows, class_rows = derive(blocks, curves)
    if (root / BANDS_TSV).read_text(encoding="utf-8") != _tsv_text(band_rows):
        problems.append("bands.tsv is not the derivation of blocks.tsv")
    if (root / CLASSES_TSV).read_text(encoding="utf-8") != _tsv_text(class_rows):
        problems.append(
            "classification.tsv is not the derivation of blocks.tsv and curves.tsv"
        )
    return problems


def task_list(root: Path) -> list[Task]:
    return [
        Task(count, replicate, str(root))
        for count in TRAJECTORY_COUNTS
        for replicate in range(REPLICATES)
    ]


def dry_run(root: Path | None = None) -> dict[str, Any]:
    """The plan, checked and counted, without spending a seed."""
    root = root or repo_root()
    tasks = task_list(root)
    return {
        "construction": check_construction(root),
        "worker_jobs": len(tasks),
        "maboss_tasks": {
            str(c): len(plan_for(c)) * REPLICATES for c in TRAJECTORY_COUNTS
        },
        "maboss_tasks_total": sum(len(plan_for(t.trajectory_count)) for t in tasks),
        "seed_ranges": {
            str(c): [replicate_seed(0, c), replicate_seed(REPLICATES - 1, c) + c - 1]
            for c in TRAJECTORY_COUNTS
        },
        "phase_durations": {p.key: phase_duration(root, p) for p in phase_plan()},
    }


# ---------------------------------------------------------------------------
# Section 12: the attempt journal. Seeds are reserved before dispatch, and a
# dispatched task counts as spent whether or not it finished.

JOURNAL_DIR = OUTPUT_DIR / "attempts"
VALIDATION_LEVEL = "full_preregistered_execution"
OUTPUTS = (CLASSES_TSV, BANDS_TSV, BLOCKS_TSV, CURVES_TSV)
ENVIRONMENT_PACKAGES = ("maboss", "cmaboss", "numpy", "pandas", "scipy")


class SeedReuseError(RuntimeError):
    """A planned seed was reserved by an earlier attempt."""


def seed_range(task: Task) -> list[int]:
    first = replicate_seed(task.replicate, task.trajectory_count)
    return [first, first + task.trajectory_count - 1]


def _fsync_directory(directory: Path) -> None:
    """Flush a directory entry, so a rename or creation in it survives a crash."""
    import os

    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def ensure_durable_directory(directory: Path) -> None:
    """Make ``directory`` exist durably.

    Every missing level is created one at a time, outermost first, and after
    each creation the directory that contains the new entry is fsynced. A level
    another process creates concurrently is treated as newly created and its
    container is fsynced too. A directory that already exists needs nothing.
    """
    directory = Path(directory)
    missing = []
    probe = directory
    while not probe.is_dir():
        missing.append(probe)
        if probe.parent == probe:
            break
        probe = probe.parent
    for level in reversed(missing):
        try:
            level.mkdir()
        except FileExistsError:
            if not level.is_dir():
                raise
        _fsync_directory(level.parent)


def _write_json_durably(path: Path, payload: dict[str, Any]) -> None:
    """Ensure the parent durably, write + fsync, rename, fsync the directory."""
    import os

    ensure_durable_directory(path.parent)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    _fsync_directory(path.parent)


def reserved_ranges(root: Path) -> list[dict[str, Any]]:
    """Every seed range any earlier attempt reserved, whatever its status."""
    out = []
    for path in sorted((root / JOURNAL_DIR).glob("attempt_*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        for r in record["reserved_seed_ranges"]:
            out.append({**r, "attempt_id": record["attempt_id"]})
    return out


RESERVATION_LOCK = JOURNAL_DIR / ".reservation.lock"


def reserve_attempt(root: Path, tasks: list[Task], provenance: dict[str, Any]) -> Path:
    """Atomically: refuse any overlap with an earlier reservation, then journal.

    The check and the journal write happen under one exclusive ``flock`` on
    ``RESERVATION_LOCK``, so two concurrent attempts cannot both see no
    reservation. The lock is released only after the journal is durably on disk.
    """
    import fcntl

    lock_path = root / RESERVATION_LOCK
    ensure_durable_directory(lock_path.parent)
    with lock_path.open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            return _check_and_reserve(root, tasks, provenance)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _check_and_reserve(
    root: Path, tasks: list[Task], provenance: dict[str, Any]
) -> Path:
    """Only ever called with ``RESERVATION_LOCK`` held."""
    import datetime

    present = [str(p) for p in (*OUTPUTS, SETTINGS_JSON) if (root / p).exists()]
    if present:
        # A canonical result set means the pre-registered seeds were spent. If
        # its ledger is absent or inconsistent, nothing proves otherwise, so the
        # owner must intervene (a dated addendum); seeds are never assumed unused.
        state = "consistent with its ledger"
        if (root / SETTINGS_JSON).is_file():
            try:
                manifest = json.loads(
                    (root / SETTINGS_JSON).read_text(encoding="utf-8")
                )
                if journal_problems(manifest, root, COMPLETED):
                    state = "without a matching COMPLETED ledger"
            except (ValueError, TypeError, KeyError, IndexError, AttributeError):
                state = "with an unreadable manifest or ledger"
        else:
            state = "without a manifest"
        raise SeedReuseError(
            f"canonical C3a outputs already exist ({', '.join(present)}), {state}. The "
            "pre-registered seeds are treated as spent: a rerun needs owner intervention "
            "and a dated addendum with fresh, disjoint seed ranges."
        )
    planned = [
        {
            "trajectory_count": t.trajectory_count,
            "replicate": t.replicate,
            "seeds": seed_range(t),
        }
        for t in tasks
    ]
    for earlier in reserved_ranges(root):
        for mine in planned:
            a, b = earlier["seeds"], mine["seeds"]
            if a[0] <= b[1] and b[0] <= a[1]:
                raise SeedReuseError(
                    f"seeds {b} are already reserved by {earlier['attempt_id']}. Spent "
                    "seeds are never reused: a rerun needs a dated addendum to the "
                    "pre-registration with fresh, disjoint seed ranges."
                )
    stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%S%fZ")
    attempt_id = f"attempt_{stamp}"
    path = root / JOURNAL_DIR / f"{attempt_id}.json"
    if path.exists():
        raise SeedReuseError(f"{path} already exists")
    _write_json_durably(
        path,
        {
            "attempt_id": attempt_id,
            "status": "RESERVED",
            "preregistration": GOVERNING_SPECIFICATION,
            "provenance_at_start": provenance,
            "reserved_seed_ranges": planned,
            "spent_seed_ranges": [],
            "completed_blocks": [],
            "error": None,
        },
    )
    return path


def _update(path: Path, **fields: Any) -> dict[str, Any]:
    record = json.loads(path.read_text(encoding="utf-8"))
    record.update(fields)
    _write_json_durably(path, record)
    return record


def _process_map(workers: int):
    def run(fn, tasks):
        with ProcessPoolExecutor(max_workers=workers, max_tasks_per_child=1) as pool:
            return list(pool.map(fn, tasks))

    return run


def execute_attempt(
    root: Path,
    tasks: list[Task],
    provenance: dict[str, Any],
    runner,
    map_fn,
    finalize,
    validate,
) -> dict[str, Any]:
    """Reserve, dispatch, finalise, validate, complete; journal FAILED on any exception.

    States: RESERVED -> DISPATCHED -> SIMULATED -> FINALIZING -> COMPLETED, or
    FAILED. Every state keeps the seed ranges reserved, so a crash at any
    transition leaves them unusable. COMPLETED is written only after
    ``validate(FINALIZING)`` has accepted the manifest and journal, and the
    accepted state is validated once more as COMPLETED.
    """
    import traceback

    journal = reserve_attempt(root, tasks, provenance)
    try:
        # Conservative: every task is spent from the moment it is dispatched.
        _update(
            journal,
            status="DISPATCHED",
            spent_seed_ranges=json.loads(journal.read_text())["reserved_seed_ranges"],
        )
        results = map_fn(runner, tasks)
        _update(
            journal,
            status="SIMULATED",
            completed_blocks=[
                {"trajectory_count": r["trajectory_count"], "replicate": r["replicate"]}
                for r in results
            ],
        )
        manifest = finalize(results, journal)
        _update(
            journal,
            status=FINALIZING,
            outputs_sha256=manifest.get("outputs_sha256", {}),
        )
        problems = validate(FINALIZING)
        if problems:
            raise RuntimeError("C3a result does not validate: " + "; ".join(problems))
        _update(journal, status=COMPLETED)
        problems = validate(COMPLETED)
        if problems:
            raise RuntimeError(
                "C3a completed result does not validate: " + "; ".join(problems)
            )
        return manifest
    except BaseException as error:
        _update(
            journal,
            status="FAILED",
            error={
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
            },
        )
        raise


# ---------------------------------------------------------------------------
# The provenance manifest and its journal: one object, validated by rebuilding.
#
# The schema is closed. Every field ``build_manifest`` emits is in exactly one
# of two sets:
#
# * RECONSTRUCTED_FIELDS are rebuilt from primary sources (the module's frozen
#   constants, the protocols, the outputs on disk) and must match exactly;
# * RUN_VARYING_FIELDS legitimately differ between runs, and each has its own
#   rule in ``_run_varying_problems``, cross-checked against git and the journal.
#
# ``set(manifest) == MANIFEST_FIELDS`` is required first, so a newly emitted
# field cannot escape validation.

RECONSTRUCTED_FIELDS = frozenset(
    {
        "artifact",
        "preregistration",
        "model_version",
        "readouts",
        "pairs",
        "construction",
        "converged_phase_horizon",
        "replicates",
        "trajectory_counts",
        "governing_trajectory_count",
        "seeds_per_block",
        "delta",
        "t19",
        "q",
        "snap",
        "time_settings",
        "validation_level",
        "claim_boundary",
        "classes",
        "outputs_sha256",
    }
)
RUN_VARYING_FIELDS = frozenset(
    {
        "attempt_id",
        "binding",
        "input_sha256_at_end",
        "workers",
        "environment",
        "warnings",
        "errors",
        "elapsed_seconds",
    }
)
MANIFEST_FIELDS = RECONSTRUCTED_FIELDS | RUN_VARYING_FIELDS
BINDING_FIELDS = frozenset(
    {
        "prereg_commit",
        "addendum_commit",
        "start_head",
        "start_tree",
        "start_dirty_paths",
        "input_sha256_at_start",
    }
)
ARTIFACT = "c3a_kinetic_readouts"
COMPLETED = "COMPLETED"
FINALIZING = "FINALIZING"


def environment() -> dict[str, str]:
    from importlib import metadata

    versions = {"python": platform.python_version(), "platform": platform.platform()}
    for package in ENVIRONMENT_PACKAGES:
        versions[package] = metadata.version(package)
    return versions


def time_settings(root: Path) -> dict[str, Any]:
    from dt_adoc.simulation.runner import _default_time_tick

    return {
        "time_tick": _default_time_tick(root),
        "max_time_per_phase": {p.key: phase_duration(root, p) for p in phase_plan()},
        "time_semantics": "dimensionless MaBoSS relative time; no physical-time mapping",
    }


def expected_seeds_per_block() -> list[dict[str, int]]:
    return [
        {"trajectory_count": c, "replicate": r, "seed": replicate_seed(r, c)}
        for c in TRAJECTORY_COUNTS
        for r in range(REPLICATES)
    ]


def expected_seed_ranges() -> list[dict[str, Any]]:
    return [
        {
            "trajectory_count": c,
            "replicate": r,
            "seeds": [replicate_seed(r, c), replicate_seed(r, c) + c - 1],
        }
        for c in TRAJECTORY_COUNTS
        for r in range(REPLICATES)
    ]


def expected_blocks() -> list[dict[str, int]]:
    return [
        {"trajectory_count": c, "replicate": r}
        for c in TRAJECTORY_COUNTS
        for r in range(REPLICATES)
    ]


def _key(entry: dict[str, Any]) -> tuple[int, int]:
    return (entry["trajectory_count"], entry["replicate"])


def _classes_from_tsv(root: Path) -> dict[str, str]:
    import csv

    with (root / CLASSES_TSV).open(encoding="utf-8", newline="") as handle:
        return {
            f"{r['pair']}:{r['readout']}": r["class"]
            for r in csv.DictReader(handle, delimiter="\t")
        }


def reconstructed_fields(root: Path, reference_root: Path) -> dict[str, Any]:
    """RECONSTRUCTED_FIELDS rebuilt from primary sources.

    ``root`` holds the outputs; ``reference_root`` is the repository whose frozen
    protocols fix the construction and the time settings.
    """
    return {
        "artifact": ARTIFACT,
        "preregistration": GOVERNING_SPECIFICATION,
        "model_version": MODEL_VERSION,
        "readouts": {"primary": PRIMARY_READOUT, "secondary": SECONDARY_READOUT},
        "pairs": {k: list(v) for k, v in PAIRS.items()},
        "construction": check_construction(reference_root),
        "converged_phase_horizon": CONVERGED_PHASE_HORIZON,
        "replicates": REPLICATES,
        "trajectory_counts": list(TRAJECTORY_COUNTS),
        "governing_trajectory_count": GOVERNING_TRAJECTORIES,
        "seeds_per_block": expected_seeds_per_block(),
        "delta": DELTA,
        "t19": T19,
        "q": Q,
        "snap": SNAP,
        "time_settings": time_settings(reference_root),
        "validation_level": VALIDATION_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "classes": _classes_from_tsv(root),
        "outputs_sha256": {str(p): _sha((root / p).read_bytes()) for p in OUTPUTS},
    }


def _binding_problems(binding: Any, end: Any, reference_root: Path) -> list[str]:
    """B8: the binding must resolve through git to the run's immutable inputs."""
    import re

    if not isinstance(binding, dict) or set(binding) != BINDING_FIELDS:
        return ["binding: fields are not exactly " + ", ".join(sorted(BINDING_FIELDS))]
    problems = []
    if binding["prereg_commit"] != PREREG_COMMIT:
        problems.append("binding: prereg_commit is not the pre-registration commit")
    if binding["addendum_commit"] != ADDENDUM_COMMIT:
        problems.append("binding: addendum_commit is not the addendum 01 commit")
    head, tree = str(binding["start_head"]), str(binding["start_tree"])
    sha1 = re.compile(r"[0-9a-f]{40}")
    if not sha1.fullmatch(head) or not sha1.fullmatch(tree):
        return problems + ["binding: start_head or start_tree is not a full object id"]
    kind = subprocess.run(
        ["git", "cat-file", "-t", head],
        cwd=reference_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if kind.returncode != 0 or kind.stdout.strip() != "commit":
        return problems + [
            f"binding: start_head {head[:12]} does not resolve to a commit"
        ]
    actual_tree = _git(reference_root, "rev-parse", f"{head}^{{tree}}").strip()
    if actual_tree != tree:
        problems.append(
            f"binding: start_tree is not the tree of start_head ({actual_tree[:12]})"
        )
    expected = input_hashes(reference_root, head)
    if binding["input_sha256_at_start"] != expected:
        problems.append(
            "binding: input_sha256_at_start does not match the files at start_head"
        )
    frozen = {
        p: _sha(_Source(reference_root, frozen_commit(p)).read(p))
        for p in bound_paths(reference_root)
    }
    if expected["bound"] != frozen:
        problems.append(
            "binding: bound inputs at start_head differ from the pre-registration commit"
        )
    if end != expected:
        problems.append("input_sha256_at_end does not match the files at start_head")
    dirty = binding["start_dirty_paths"]
    watched = set(expected["bound"]) | set(expected["generator"])
    if not isinstance(dirty, list) or any(
        line[3:] in watched or line[3:].startswith(GENERATOR_PACKAGE)
        for line in map(str, dirty)
    ):
        problems.append("binding: a bound or generator file was dirty at start")
    return problems


def journal_problems(
    manifest: dict[str, Any], root: Path, required_status: str
) -> list[str]:
    """B9: the journal named by attempt_id is part of the canonical result."""
    import re

    attempt_id = str(manifest.get("attempt_id"))
    if not re.fullmatch(r"attempt_\d{8}T\d{12}Z", attempt_id):
        return ["attempt_id is not a journal attempt id"]
    matches = sorted((root / JOURNAL_DIR).glob(f"{attempt_id}.json"))
    if len(matches) != 1:
        return [f"journal {attempt_id}.json is missing"]
    journal = json.loads(matches[0].read_text(encoding="utf-8"))
    problems = []
    if journal.get("attempt_id") != attempt_id:
        problems.append("journal: attempt_id does not match the manifest")
    if journal.get("status") != required_status:
        problems.append(
            f"journal: status is {journal.get('status')}, not {required_status}"
        )
    if journal.get("error") is not None:
        problems.append("journal: records an error")
    if journal.get("preregistration") != GOVERNING_SPECIFICATION:
        problems.append("journal: preregistration differs")
    if journal.get("provenance_at_start") != manifest.get("binding"):
        problems.append(
            "journal: provenance_at_start differs from the manifest binding"
        )
    expected = sorted(expected_seed_ranges(), key=_key)
    for field in ("reserved_seed_ranges", "spent_seed_ranges"):
        if sorted(journal.get(field, []), key=_key) != expected:
            problems.append(
                f"journal: {field} are not exactly the pre-registered 40 ranges"
            )
    if sorted(journal.get("completed_blocks", []), key=_key) != sorted(
        expected_blocks(), key=_key
    ):
        problems.append("journal: completed_blocks are not exactly the 40 blocks")
    if journal.get("outputs_sha256") != manifest.get("outputs_sha256"):
        problems.append("journal: outputs_sha256 differ from the manifest")
    first_seeds = {
        _key(r): r["seeds"][0] for r in journal.get("reserved_seed_ranges", [])
    }
    if {_key(b): b["seed"] for b in manifest.get("seeds_per_block", [])} != first_seeds:
        problems.append(
            "journal: reserved ranges disagree with the manifest seeds_per_block"
        )
    return problems


def _run_varying_problems(
    manifest: dict[str, Any], root: Path, reference_root: Path, required_status: str
) -> list[str]:
    import re

    problems = journal_problems(manifest, root, required_status)
    problems += _binding_problems(
        manifest["binding"], manifest["input_sha256_at_end"], reference_root
    )
    workers = manifest["workers"]
    if not isinstance(workers, int) or isinstance(workers, bool) or workers < 1:
        problems.append("workers is not a positive integer")
    env = manifest["environment"]
    expected_keys = {"python", "platform", *ENVIRONMENT_PACKAGES}
    if not isinstance(env, dict) or set(env) != expected_keys:
        problems.append(
            "environment: keys are not exactly python, platform and the packages"
        )
    else:
        for key, value in env.items():
            if not isinstance(value, str) or value.strip() in (
                "",
                "unknown",
                "unavailable",
            ):
                problems.append(
                    f"environment: {'MaBoSS' if key == 'maboss' else key} not recorded"
                )
        if not re.fullmatch(r"\d+\.\d+\.\d+", env["python"]):
            problems.append("environment: python is not an exact X.Y.Z version")
    warnings_ = manifest["warnings"]
    if not isinstance(warnings_, dict) or not all(
        isinstance(k, str) and isinstance(v, int) and not isinstance(v, bool) and v >= 1
        for k, v in warnings_.items()
    ):
        problems.append("warnings is not a message -> positive count mapping")
    if manifest["errors"] != []:
        problems.append("errors is not empty")
    elapsed = manifest["elapsed_seconds"]
    if (
        not isinstance(elapsed, (int, float))
        or isinstance(elapsed, bool)
        or elapsed < 0
    ):
        problems.append("elapsed_seconds is not a non-negative number")
    return problems


def manifest_problems(
    manifest: Any, root: Path, reference_root: Path, required_status: str = COMPLETED
) -> list[str]:
    """Every problem with a canonical result; [] only when it rebuilds exactly."""
    if not isinstance(manifest, dict):
        return ["manifest is not a mapping"]
    if set(manifest) != MANIFEST_FIELDS:
        missing = sorted(MANIFEST_FIELDS - set(manifest))
        extra = sorted(set(manifest) - MANIFEST_FIELDS)
        return [f"manifest fields differ: missing {missing}, unexpected {extra}"]
    for path in (*OUTPUTS, SETTINGS_JSON):
        if not (root / path).is_file():
            return [f"{path} is missing"]
    expected = reconstructed_fields(root, reference_root)
    problems = [
        f"{field} does not match its reconstruction"
        for field in sorted(RECONSTRUCTED_FIELDS)
        if manifest[field] != expected[field]
    ]
    try:
        problems += outputs_problems(root, reference_root)
        problems += _run_varying_problems(
            manifest, root, reference_root, required_status
        )
    except (
        TypeError,
        KeyError,
        IndexError,
        ValueError,
        AttributeError,
        subprocess.CalledProcessError,
    ) as error:
        # A malformed value, or a bound file absent at the recorded commit, is a
        # validation failure, never a crash that could be mistaken for an
        # infrastructure error.
        problems.append(
            f"malformed manifest or journal: {type(error).__name__}: {error}"
        )
    return problems


def validate_manifest(
    root: Path | None = None,
    reference_root: Path | None = None,
    required_status: str = COMPLETED,
) -> list[str]:
    """Validate the written manifest and its journal. An accepted run is COMPLETED."""
    root = root or repo_root()
    path = root / SETTINGS_JSON
    if not path.is_file():
        return [f"{SETTINGS_JSON} is missing"]
    manifest = json.loads(path.read_text(encoding="utf-8"))
    return manifest_problems(manifest, root, reference_root or root, required_status)


def build_manifest(
    root: Path,
    reference_root: Path,
    results: list[dict[str, Any]],
    binding: dict[str, Any],
    at_end: dict[str, Any],
    workers: int,
    elapsed: float,
    attempt_id: str,
) -> dict[str, Any]:
    """The manifest, emitted as exactly MANIFEST_FIELDS."""
    warning_counts: dict[str, int] = {}
    for r in results:
        for w in r.get("warnings", []):
            warning_counts[w] = warning_counts.get(w, 0) + 1
    manifest = {
        **reconstructed_fields(root, reference_root),
        "attempt_id": attempt_id,
        "binding": binding,
        "input_sha256_at_end": at_end,
        "workers": workers,
        "environment": environment(),
        "warnings": warning_counts,
        "errors": [],
        "elapsed_seconds": elapsed,
    }
    if set(manifest) != MANIFEST_FIELDS:
        raise RuntimeError("build_manifest emitted fields outside the closed schema")
    return manifest


def _finalize(
    root: Path,
    reference_root: Path,
    binding: dict[str, Any],
    workers: int,
    started: float,
):
    """Write outputs and the manifest. Validation and COMPLETED follow in execute_attempt."""
    import time

    def finalize(results: list[dict[str, Any]], journal: Path) -> dict[str, Any]:
        at_end = input_hashes(reference_root)
        if at_end != binding["input_sha256_at_start"]:
            raise RuntimeError(
                "C3a run invalid: a bound or generator file changed during the run"
            )
        seeds = sorted(
            (
                {
                    "trajectory_count": r["trajectory_count"],
                    "replicate": r["replicate"],
                    "seed": r["seed"],
                }
                for r in results
            ),
            key=_key,
        )
        if seeds != sorted(expected_seeds_per_block(), key=_key):
            raise RuntimeError(
                "C3a run invalid: the simulated blocks are not the pre-registered 40"
            )
        comparison = compare(results)
        _write_tsv(root / CLASSES_TSV, comparison["classes"])
        _write_tsv(root / BANDS_TSV, comparison["bands"])
        _write_tsv(root / BLOCKS_TSV, comparison["blocks"])
        _write_tsv(root / CURVES_TSV, comparison["curves"])
        manifest = build_manifest(
            root,
            reference_root,
            results,
            binding,
            at_end,
            workers,
            time.time() - started,
            journal.stem,
        )
        _write_json_durably(root / SETTINGS_JSON, manifest)
        return manifest

    return finalize


def build(
    root: Path | None = None, workers: int = 3, execute: bool = False
) -> dict[str, Any]:
    """Dry run by default. ``execute=True`` binds, checks, reserves, spends and writes."""
    import functools
    import time

    root = root or repo_root()
    if not execute:
        return dry_run(root)
    binding = bind_inputs(root)
    check_construction(root)
    return execute_attempt(
        root,
        task_list(root),
        binding,
        run_block,
        _process_map(workers),
        _finalize(root, root, binding, workers, time.time()),
        functools.partial(validate_manifest, root, root),
    )


if __name__ == "__main__":  # pragma: no cover
    import sys

    execute = "--execute" in sys.argv
    numbers = [a for a in sys.argv[1:] if a.isdigit()]
    print(
        json.dumps(
            build(workers=int(numbers[0]) if numbers else 3, execute=execute),
            indent=2,
            default=str,
        )[:4000]
    )
