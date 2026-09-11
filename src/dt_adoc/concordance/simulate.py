"""Regenerate the simulated side of the concordance comparison, with provenance.

`docs/results_reproducibility_matrix.tsv` carries a ``simulated_value`` column
that was typed in, and the run it came from lived under `output/`, which is
gitignored. Nothing tracked in the repository backed any of those numbers, and
the narrative's pointer to ``output/reproducibility/run_settings.json`` names a
file that does not exist. This module closes that gap: it re-runs the arms from
the committed model and writes both the values and the settings that produced
them into tracked artifacts.

Two horizons, never merged. The declared horizon is what `config/protocols.yaml`
actually configures; the converged horizon is a run-time override that reads each
phase at its logical fixed point. The declared horizon reads the adhesion
endpoints roughly 4000x before that fixed point
(`docs/endpoint_convergence_finding.md`), so a single unlabelled probability
would be actively misleading and every record here carries its horizon class.

One uncertainty is recorded, and it is not a confidence interval.

The **across-seed spread** is how much the estimate moves when only the random
stream changes. For this model it is frequently exactly zero. A zero seed spread
is *not* evidence that the estimate is exact, and five seeds bound gross
instability rather than estimating a variance.

A second quantity used to be recorded beside it -- the binomial plug-in
`sqrt(p(1-p)/n)` over the pooled draws, carried as `node_trajectory_se` and
emitted as a `simulated_trajectory_se` column. **It is withdrawn in full**, and
the reason is now positive rather than negative. `docs/maboss_estimator_semantics.md`
reads the estimator from pinned MaBoSS source: a reported node value is
accumulated dwell TIME divided by `(tick x trajectories)`, so the per-trajectory
contribution is a continuous occupancy fraction, not a Bernoulli indicator.
Binomial variance describes a sum of indicators, so the plug-in is not a loose
estimate of this quantity's sampling error -- it is the **wrong variance family**
(that document, section 3d). A number that is the wrong family cannot be
rehabilitated by calling it a diagnostic, and a column whose name ends in `_se`
invites exactly the reading the analysis has withdrawn three times.

Nothing is lost by removing it. It was a deterministic function of `node_mean`
and `trajectory_count x len(seeds)`, both of which this record still carries, so
any reader who wants the old number can recompute it -- and would then be
computing something this repository says is inapplicable.

This withdrawal is scoped to the SIMULATOR's occupancy estimates. Binomial and
Wilson intervals on **experimental counts** are untouched and remain correct:
`figure.py` reports a Wilson 95% interval on 9/19 attached blastocysts and that
is exactly the right tool for counting embryos.

A third attempt to say more than this was made and is withdrawn in full. It
committed a probe that measured the declared-horizon difference between the
as-built chain and one with the bypassed maternal phase inserted, and drew a
mechanism from the continuation support and mass it recorded. Neither quantity
could carry that: `project_joint_distribution` renormalises the retained
distribution to 1, so the recorded mass was `1.0` by construction and measured
nothing, and a support of a few thousand states is compatible with almost all the
weight on one of them. The probe and every conclusion from it are removed.

So neither a binomial standard error nor a `1/trajectory_count` resolution limit
is justified here, and earlier revisions of this module asserted each in turn.
**Near-zero differences are therefore reported as uncharacterised**: the values
are recorded, and no claim is made about whether a difference between them is
resolvable. A classification that needs such a claim is not made at all -- R43a
rests on horizon instability: the arm's across-seed spread is the size of
its value, which needs no error model either.

Neither quantity bounds model uncertainty or observation uncertainty, and neither
may be presented as a confidence interval on a biological quantity.
"""

from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev

from dt_adoc.model.provenance import repo_root
from dt_adoc.protocols.conditions import get_protocol
from dt_adoc.simulation.runner import (
    _maboss_python_package_version,
    protocol_continuation,
    run_protocol,
)

#: The horizon override that reads each protocol phase at its logical fixed
#: point. Same value the README animation uses, so the two artifacts describe the
#: same simulation regime. Dimensionless MaBoSS relative time, never a day count.
CONVERGED_PHASE_HORIZON = 25.0

#: Trajectories per run. Matches the README animation so the figure and the
#: animation are not two different simulations of the same model.
DEFAULT_TRAJECTORIES = 20_000

#: Five seeds is enough to show the Monte Carlo spread is far smaller than every
#: disagreement reported here, which is the only claim the spread supports.
DEFAULT_SEEDS = (1, 2, 3, 4, 5)

HORIZON_CLASSES = ("declared", "converged")


@dataclass(frozen=True)
class ArmRun:
    """One arm, one horizon, aggregated over seeds."""

    arm_id: str
    protocol_id: str
    #: The protocol chain actually executed, in order, ending at
    #: ``protocol_id``. Recorded because ``protocol_id`` alone does NOT identify
    #: what was simulated: a protocol's meaning depends on the state its phase
    #: began in, and that is set by everything upstream of it. An external reader
    #: asked whether the mifepristone arm traverses the maternal mifepristone
    #: phase, and no tracked artifact could answer -- the chain was recoverable
    #: only by re-resolving `config/protocols.yaml` through the superset clone
    #: layer in `protocols/conditions.py`. It is a fact of the run, so it belongs
    #: in the run record.
    lineage: tuple[str, ...]
    horizon_class: str
    #: Mean P(node = ON) across seeds, per tracked node.
    node_mean: dict[str, float]
    #: Population standard deviation across seeds, per tracked node. This is how
    #: much the estimate moves when only the random stream changes, and it is
    #: frequently exactly zero here. Zero does not mean exact.
    node_sd: dict[str, float]
    #: Per-seed values, kept so a reader can check the aggregate.
    node_by_seed: dict[str, list[float]]
    seeds: tuple[int, ...]
    trajectory_count: int
    phase_horizon: float | None


@dataclass(frozen=True)
class RunProvenance:
    """Everything needed to decide whether a rerun should match."""

    model_version: str
    git_commit: str
    git_tree_dirty: bool
    #: Content digest of the generating implementation, and the exact file list
    #: it covers. Recomputable from the tree: none of these files is written by
    #: the run, so a reader can rerun the digest and compare.
    implementation_digest: str
    implementation_files: tuple[str, ...]
    network_bnd_sha256: str
    baseline_cfg_sha256: str
    protocols_yaml_sha256: str
    #: Every condition .cfg ``run_protocol`` loads, hashed. These carry the
    #: istates and rates, so a concordance number can change when one changes
    #: while all three hashes above stay identical.
    condition_cfg_sha256: dict[str, str]
    maboss_python_version: str
    python_version: str
    trajectory_count: int
    seeds: tuple[int, ...]
    converged_phase_horizon: float
    time_tick: float


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(args: list[str], root: Path) -> str:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        return "unavailable"


#: The implementation whose content decides every number here: the concordance
#: package plus the simulation, protocol and model code it drives. Pinned by
#: content because on the run that first produces these artifacts the concordance
#: package is entirely uncommitted, so ``git_commit`` alone identifies none of it.
#: The intervention engine and its library are included because the runner
#: renders every network the library covers through them. The MaBoSS adapter is
#: included because it renders the executed network and projects and applies the
#: joint state carried from one protocol phase into the next.
IMPLEMENTATION_GLOBS = (
    "src/dt_adoc/concordance/*.py",
    "src/dt_adoc/maboss_adapter.py",
    "src/dt_adoc/simulation/*.py",
    "src/dt_adoc/protocols/*.py",
    "src/dt_adoc/model/*.py",
    "src/dt_adoc/calibration/*.py",
    "src/dt_adoc/reporting/structure.py",
    "src/dt_adoc/perturbations/engine.py",
    "src/dt_adoc/perturbations/adjudication.py",
    "config/intervention_library.tsv",
    "config/direct_effect_adjudications.tsv",
    "config/direct_effect_target_policy.tsv",
    "config/node_entity_map.tsv",
    "config/direct_effect_target_declarations.tsv",
    # Read by the direct-row licence and run record (Stage 4b §6.1 item 5,
    # §6.5): the expressivity generator, what it reads beyond the globs above,
    # and the two tables it must reproduce (amendment A1,
    # docs/stage4b_implementation.md).
    "src/dt_adoc/reporting/veto_expressivity.py",
    "config/observation_model_map.tsv",
    "docs/stage4b/v060_veto_expressivity.tsv",
    "docs/stage4b/v060_veto_invariance.tsv",
)


def implementation_files(root: Path) -> tuple[str, ...]:
    """Repository-relative paths of the code this run's numbers depend on."""
    found: set[str] = set()
    for pattern in IMPLEMENTATION_GLOBS:
        found.update(str(path.relative_to(root)) for path in sorted(root.glob(pattern)))
    return tuple(sorted(found))


def implementation_digest(root: Path, files: tuple[str, ...] | None = None) -> str:
    """Content digest of the generating implementation.

    Deliberately **not** a digest of "everything dirty". An earlier version
    hashed every path `git status` reported, which included `run_settings.json`
    and the figure -- files this very run then overwrites. That digest was
    self-referential and could never be recomputed from the committed tree, so it
    pinned nothing. This one covers source files only, none of which the run
    writes, so ``recompute == recorded`` is a check a reader can actually run and
    ``tests/unit/test_concordance.py`` does.
    """
    import hashlib

    digest = hashlib.sha256()
    for relative in files if files is not None else implementation_files(root):
        digest.update(relative.encode("utf-8"))
        path = root / relative
        digest.update(_sha256(path).encode("ascii") if path.is_file() else b"absent")
    return digest.hexdigest()


def run_provenance(
    *,
    model_version: str,
    root: Path | None = None,
    trajectory_count: int = DEFAULT_TRAJECTORIES,
    seeds: tuple[int, ...] = DEFAULT_SEEDS,
) -> RunProvenance:
    """Record the exact inputs of this concordance build.

    The three hashes are the model's executable surface: the rule set, the
    initial-condition and rate file, and the protocol schedule. A concordance
    number can change only if one of those, the trajectory count, a seed or the
    horizon changed, so recording them makes a silent drift detectable.
    """
    from dt_adoc.model.runtime import resolve_model
    from dt_adoc.simulation.runner import _default_simulation_settings

    active_root = root or repo_root()
    model = resolve_model(model_version, active_root)
    settings = _default_simulation_settings(active_root)
    impl_files = implementation_files(active_root)
    condition_hashes = {
        path.name: _sha256(path)
        for path in sorted(Path(model.condition_dir).glob("*.cfg"))
    }
    return RunProvenance(
        model_version=model_version,
        git_commit=_git(["rev-parse", "HEAD"], active_root),
        git_tree_dirty=bool(_git(["status", "--porcelain"], active_root)),
        implementation_digest=implementation_digest(active_root, impl_files),
        implementation_files=impl_files,
        condition_cfg_sha256=condition_hashes,
        network_bnd_sha256=_sha256(model.network_bnd),
        baseline_cfg_sha256=_sha256(model.baseline_cfg),
        protocols_yaml_sha256=_sha256(active_root / "config" / "protocols.yaml"),
        maboss_python_version=_maboss_python_package_version(),
        python_version=platform.python_version(),
        trajectory_count=trajectory_count,
        seeds=seeds,
        converged_phase_horizon=CONVERGED_PHASE_HORIZON,
        time_tick=float(settings["time_tick"]),
    )


def protocol_lineage(
    protocol_id: str,
    *,
    model_version: str,
    root: Path | None = None,
) -> tuple[str, ...]:
    """The declared chain of protocols ending at ``protocol_id``.

    `config/protocols.yaml` gives each protocol a ``continuation_from``, and the
    ADOC arms are sequential by design: the adhesion challenge begins from the
    state the six-day hormone protocol reached, which itself began from E2
    priming, which began from basal. ``run_protocol`` does not follow that chain
    on its own -- it records ``continuation_from`` but starts from
    ``baseline.cfg`` unless a continuation is supplied.

    Running an arm without its lineage silently reports the wrong thing at any
    finite horizon: the declared-duration readouts then describe a challenge
    applied to an unconditioned tissue rather than to a hormone-conditioned one.
    At the converged horizon the fixed point is reached regardless, which is
    exactly why the error is easy to miss.
    """
    chain: list[str] = []
    current: str | None = protocol_id
    seen: set[str] = set()
    while current is not None:
        if current in seen:
            raise ValueError(f"cyclic continuation_from at {current!r}")
        seen.add(current)
        chain.append(current)
        current = get_protocol(
            current, root, model_version=model_version
        ).continuation_from
    return tuple(reversed(chain))


def run_arm(
    arm_id: str,
    protocol_id: str,
    *,
    horizon_class: str,
    model_version: str,
    root: Path | None = None,
    trajectory_count: int = DEFAULT_TRAJECTORIES,
    seeds: tuple[int, ...] = DEFAULT_SEEDS,
) -> ArmRun:
    """Run one arm at one horizon across every seed.

    ``horizon_class='declared'`` leaves every phase at the ``relative_duration``
    the committed protocol declares. ``'converged'`` overrides every phase to
    ``CONVERGED_PHASE_HORIZON``. The declared value is never mutated on disk.
    """
    if horizon_class not in HORIZON_CLASSES:
        raise ValueError(f"unknown horizon_class {horizon_class!r}")
    phase_horizon = None if horizon_class == "declared" else CONVERGED_PHASE_HORIZON
    lineage = protocol_lineage(protocol_id, model_version=model_version, root=root)
    by_seed: dict[str, list[float]] = {}
    for seed in seeds:
        result = None
        continuation = None
        for index, step_protocol in enumerate(lineage):
            result = run_protocol(
                step_protocol,
                model_version=model_version,
                root=root,
                continuation=continuation,
                seed=seed,
                sample_count=trajectory_count,
                phase_horizon=phase_horizon,
            )
            if index + 1 < len(lineage):
                continuation = protocol_continuation(
                    lineage[index + 1],
                    result,
                    model_version=model_version,
                    root=root,
                )
        assert result is not None
        for node_id, value in result.final_result.last.items():
            by_seed.setdefault(node_id, []).append(float(value))

    node_mean = {k: mean(v) for k, v in by_seed.items()}
    return ArmRun(
        arm_id=arm_id,
        protocol_id=protocol_id,
        lineage=lineage,
        horizon_class=horizon_class,
        node_mean=node_mean,
        node_sd={k: (pstdev(v) if len(v) > 1 else 0.0) for k, v in by_seed.items()},
        node_by_seed=by_seed,
        seeds=tuple(seeds),
        trajectory_count=trajectory_count,
        phase_horizon=phase_horizon,
    )


def write_run_settings(
    provenance: RunProvenance,
    runs: list[ArmRun],
    destination: Path,
) -> Path:
    """Write the tracked settings record the narrative has been promising.

    Deliberately includes the per-seed values rather than only the aggregate: a
    reader checking whether a disagreement is Monte Carlo noise needs the spread,
    and an aggregate alone cannot be audited.
    """
    payload = {
        "schema_version": "1.0",
        "provenance": asdict(provenance),
        "arms": [
            {
                "arm_id": run.arm_id,
                "protocol_id": run.protocol_id,
                "lineage": list(run.lineage),
                "horizon_class": run.horizon_class,
                "phase_horizon": run.phase_horizon,
                "trajectory_count": run.trajectory_count,
                "seeds": list(run.seeds),
                "node_mean": run.node_mean,
                "node_sd": run.node_sd,
                "node_by_seed": run.node_by_seed,
            }
            for run in runs
        ],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return destination
