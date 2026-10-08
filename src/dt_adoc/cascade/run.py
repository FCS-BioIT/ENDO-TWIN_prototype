"""Run a perturbation-response cascade and write its bundle.

``run_cascade`` is the programmatic entry point; ``dt_adoc.cli perturb cascade``
is a thin wrapper over it. The bundle under ``output/perturbations/<run_id>/``:

- ``events.tsv``: one row per arm x trajectory x tracked node -- every node the
  run reports (every non-internal node), including those that never switch.
  That set is not the same as the nodes the starting state carries
  (``metadata.json -> starting_state -> memory_nodes``): ``tracked_nodes`` lists
  both and the tracked nodes the start does not carry, which begin from the
  condition cfg. Declared ``IN_*`` inputs are internal to the run and recorded
  per arm in ``metadata.json -> arms``;
- ``node_summary.tsv``: per arm, node and first-switch direction (every
  direction with a switch has a row);
- ``control_comparison.tsv``: perturbed vs matched control, per node;
- ``pairwise_precedence.tsv``: P(A first | both switch, order identifiable),
  perturbed arm;
- ``cascade.{png,svg,pdf}``: the response-order figure;
- ``metadata.json``: everything needed to reproduce and to bound the claim.
"""

from __future__ import annotations

import fcntl
import json
import os
import platform
import re
import shutil
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from importlib import metadata as package_metadata
from pathlib import Path
from typing import Any

import numpy as np

from dt_adoc.cascade import summary as S
from dt_adoc.cascade.annotations import annotation_sources, node_annotations
from dt_adoc.cascade.events import CATEGORIES, SNAP_TOLERANCE
from dt_adoc.cascade.figure import render_cascade
from dt_adoc.cascade.simulate import (
    SEED_SCHEME,
    PhaseSettings,
    StartSettings,
    arms_for,
    build_starting_ensemble,
    run_arm,
    sample_initial_states,
    trajectory_seeds,
    validate_memory_policy,
)
from dt_adoc.concordance.simulate import (
    implementation_files as simulation_implementation_files,
)
from dt_adoc.model.provenance import (
    describe_file,
    repo_root,
    sha256_file,
    source_commit,
)
from dt_adoc.model.runtime import resolve_model
from dt_adoc.perturbations.spec import (
    PerturbationSpec,
    effect_provenance,
    validate_spec,
)
from dt_adoc.protocols.conditions import protocol_file

SCHEMA = "dt_adoc.perturbation_cascade/1"
ANALYSIS_VERSION = "1.0.0"
OUTPUT_ROOT = Path("output/perturbations")
DEFAULT_POSITION = "normalized_time"

EVENT_DEFINITION = {
    "first_switch": "first departure of the node from its state at the perturbation boundary (t = 0), read off single-trajectory tick occupancies (dt_adoc.cascade.events); exact when the window holds one switch",
    "n_switches_min": "minimum number of switches consistent with the tick occupancies; a lower bound",
    "net_change": "final state at the horizon differs from the starting state",
    "transient_return": "switched at least twice and ended in the starting state",
    "rule_disagrees_at_horizon": "the node's executed rule calls for a different value in the final state: still at risk, so a missing switch is censored",
    "categories": list(CATEGORIES),
    "categories_note": "categories are read off n_switches_min, a lower bound: net_change_n_switches_min_1 is consistent with one switch, not proof of one; a fractional window can hide out-and-back pairs. Net change, whole windows and first-switch windows are exact",
    "snap_tolerance": SNAP_TOLERANCE,
    "validation": "docs/perturbation_cascade/README.md (Stage A)",
}
CLAIMS = {
    "result_kind": "conditional_model_internal_prediction",
    "experimentally_validated": False,
    "time_calibrated": False,
    "time_semantics": "dimensionless continuous time of the asynchronous stochastic MaBoSS dynamics, every transition rate 1; not calibrated to hours or days, not a count of Boolean updates",
    "individual_counterfactual": False,
    "screenability_claim": False,
    "screenability_note": "transient or whole-state differences are not screenability (docs/stage4b_direct_admission.md, owner decision 6); this output does not license a screen",
    "intervals": "position bars are empirical quantiles across trajectories, not confidence intervals; *_ci_* columns are percentile bootstraps over trajectories treated as exchangeable",
}
#: What has and has not been validated, recorded with every run.
VALIDATION_LEVEL = {
    "level": "exploratory_model_internal",
    "validated": "event reconstruction from tick occupancies against the installed MaBoSS backend (docs/perturbation_cascade/README.md, Stage A)",
    "not_validated": "biological timing, causal order and experimental response; no ADOC measurement is compared",
}
#: The strongest statement a run supports; the detail is in ``claims``.
CLAIM_CEILING = {
    "ceiling": CLAIMS["result_kind"],
    "statement": "simulated first-switch order and frequencies in dimensionless MaBoSS time against a matched control, conditional on the model's rules and the stated starting ensemble",
    "see": "claims",
}

NONSTATIONARY_CONTROL_WARNING = (
    "the matched control switched; the starting state is not a fixed point of the "
    "start protocol's dynamics, so perturbed-arm switches mix relaxation with "
    "response. Read control_comparison.tsv."
)


def run_warnings(diagnostics: dict[str, Any]) -> list[str]:
    """Warnings a reader must see with the result; persisted in metadata.json."""
    warnings = []
    if not diagnostics["control_stationary"]:
        warnings.append(NONSTATIONARY_CONTROL_WARNING)
    return warnings


@dataclass(frozen=True)
class CascadeRequest:
    spec: PerturbationSpec
    n_trajectories: int = 2000
    master_seed: int = 20261008
    start: StartSettings = field(default_factory=StartSettings)
    phase: PhaseSettings = field(default_factory=PhaseSettings)
    position: str = DEFAULT_POSITION
    workers: int = 4
    run_id: str | None = None
    overwrite: bool = False
    """Replace an existing bundle of the same run id (its files only)."""


def _versions() -> dict[str, str]:
    out = {"python": platform.python_version()}
    for name in ("maboss", "cmaboss", "numpy", "pandas", "matplotlib", "pyyaml"):
        try:
            out[name] = package_metadata.version(name)
        except package_metadata.PackageNotFoundError:
            out[name] = "unavailable"
    return out


def _subtitle(req: CascadeRequest, ensemble, n: int, diagnostics: dict) -> str:
    spec = req.spec
    effects = []
    for k, v in sorted(spec.input_changes.items()):
        effects.append(
            f"{k} {'ON' if ensemble.step_inputs.get(k) else 'OFF'} -> {'ON' if v else 'OFF'}"
        )
    effects += [f"intervention {i}" for i in spec.interventions]
    effects += [f"rule variant {f}={v}" for f, v in sorted(spec.rule_variants.items())]
    c = diagnostics["control"]
    control = (
        "matched control: no node switched in any trajectory (start is a fixed point)"
        if diagnostics["control_stationary"]
        else f"matched control: switches in {c['fraction_trajectories_with_any_switch']:.0%} of trajectories, see control_comparison.tsv"
    )
    return (
        f"{spec.model_version} · start: end of {' -> '.join(ensemble.lineage)} (lineage horizon {req.start.init_horizon}, "
        f"{req.start.memory_policy} carried) · perturbation at t = 0: {'; '.join(effects)}\n"
        f"{n} paired trajectories per arm (perturbed and matched unperturbed control share each starting state and seed) · "
        f"observed to t = {req.phase.horizon} (MaBoSS relative time, not hours)\n{control}\n"
        "dot = median, thick bar = middle 50 %, thin line = middle 95 % of trajectories in which the node switched that way "
        "(empirical spread, not a confidence interval) · bold = phenotype readout\n"
        "[ ] = marker genes the repository reads the node through, not its definition · = f( ) = composite node, inputs of its rule"
    )


def run_cascade(
    req: CascadeRequest, root: Path | None = None, out_root: Path | None = None
) -> Path:
    active_root = root or repo_root()
    commit = source_commit(active_root)  # before anything is written
    started = time.time()
    spec = req.spec
    validate_spec(spec, active_root)
    validate_memory_policy(spec.model_version, req.start.memory_policy, active_root)
    if req.position not in S.POSITIONS:
        raise ValueError(f"position must be one of {S.POSITIONS}")
    run_id = req.run_id or f"{spec.name}__n{req.n_trajectories}__seed{req.master_seed}"
    final = bundle_directory(
        out_root or active_root / OUTPUT_ROOT, run_id, overwrite=req.overwrite
    )
    # Written into a staging directory and swapped in only once complete, so
    # a failure never leaves new tables beside an old bundle's provenance.
    out = begin_staging(final)
    try:
        ensemble = build_starting_ensemble(spec, req.start, active_root)
        states = sample_initial_states(ensemble, req.n_trajectories, req.master_seed)
        seeds = trajectory_seeds(req.master_seed, req.n_trajectories)
        perturbed_arm, control_arm = arms_for(spec, ensemble)
        results = {
            arm.name: run_arm(
                ensemble,
                arm,
                states,
                seeds,
                req.phase,
                workers=req.workers,
                root=active_root,
            )
            for arm in (perturbed_arm, control_arm)
        }
        pert, ctrl = results["perturbed"].events, results["control"].events

        import pandas as pd

        events = pd.concat([pert, ctrl], ignore_index=True)
        events.to_csv(out / "events.tsv", sep="\t", index=False)
        summaries = []
        for name, ev in (("perturbed", pert), ("control", ctrl)):
            s = S.node_summary(ev)
            s.insert(0, "arm", name)
            summaries.append(s)
        node_summary = pd.concat(summaries, ignore_index=True)
        node_summary.to_csv(out / "node_summary.tsv", sep="\t", index=False)
        comparison = S.compare_arms(pert, ctrl)
        comparison.to_csv(out / "control_comparison.tsv", sep="\t", index=False)
        precedence = S.pairwise_precedence(pert)
        precedence.to_csv(out / "pairwise_precedence.tsv", sep="\t", index=False)

        diagnostics = run_diagnostics(pert, ctrl)
        warnings = run_warnings(diagnostics)
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        annotations = node_annotations(spec.model_version, active_root)
        figure_paths = [out / f"cascade.{ext}" for ext in ("png", "svg", "pdf")]
        render_cascade(
            node_summary[node_summary.arm == "perturbed"],
            node_summary[node_summary.arm == "control"],
            precedence,
            annotations,
            position=req.position,
            title=f"Simulated response order after: {spec.description or spec.name}",
            subtitle=_subtitle(req, ensemble, req.n_trajectories, diagnostics),
            footer=(
                "Model-conditional simulation of stochastic Boolean dynamics. Not measured timing, not a causal sequence, "
                "not a clinical or screening claim. Read order claims from pairwise_precedence.tsv."
            ),
            paths=figure_paths,
        )

        spec_model = resolve_model(spec.model_version, active_root)
        meta: dict[str, Any] = {
            "schema": SCHEMA,
            "analysis_version": ANALYSIS_VERSION,
            "run_id": run_id,
            "source_commit": commit,
            "command": sys.argv,
            "claims": CLAIMS,
            "claim_ceiling": CLAIM_CEILING,
            "validation_level": VALIDATION_LEVEL,
            "warnings": warnings,
            "perturbation": {
                "spec": spec.to_dict(),
                "effects": effect_provenance(spec, active_root),
                "provenance_classes": sorted(
                    {
                        e["provenance_class"]
                        for e in effect_provenance(spec, active_root)
                    }
                ),
            },
            "model": {
                "model_version": spec.model_version,
                "network_bnd": describe_file(
                    spec_model.network_bnd, root=active_root
                ).__dict__,
                "baseline_cfg": describe_file(
                    spec_model.baseline_cfg, root=active_root
                ).__dict__,
                "node_dictionary": describe_file(
                    spec_model.node_dictionary, root=active_root
                ).__dict__,
                "protocols": describe_file(
                    active_root / protocol_file(spec.model_version, active_root),
                    root=active_root,
                ).__dict__,
            },
            "starting_state": ensemble.record(active_root),
            "tracked_nodes": {
                "nodes": sorted(pert.node.unique()),
                "not_carried_by_the_start": sorted(
                    set(pert.node.unique()) - set(ensemble.continuation.node_ids)
                ),
                "note": "events.tsv covers every node the run reports (every non-internal "
                "node). A tracked node the start does not carry begins from the condition "
                "cfg, and its t = 0 state is read from the first tick window, or the run is "
                "refused if that window is fractional",
            },
            "arms": {
                name: {
                    "input_states": dict(sorted(r.arm.input_states.items())),
                    "interventions": list(r.arm.interventions),
                    "rule_variants": dict(r.arm.rule_variants),
                    "executed_network": r.executed_network,
                }
                for name, r in results.items()
            },
            "perturbation_boundary": "t = 0 of the perturbed phase; both arms start from the same sampled terminal state of the start protocol; input values and interventions are held for the whole phase",
            "unchanged": "every input and every intervention active at the end of the start protocol stays active in both arms unless the spec changes it",
            "simulation": {
                "n_trajectories_per_arm": req.n_trajectories,
                "master_seed": req.master_seed,
                "seed_scheme": SEED_SCHEME,
                "seeds_recorded_in": "events.tsv (seed column)",
                "random_generator": "MaBoSS default pseudorandom generator (Rand48; use_physrandgen FALSE)",
                "independence": "initial states i.i.d. by construction; event streams from distinct spread seeds, not proven independent",
                "phase": asdict(req.phase),
                "horizon_semantics": "dimensionless MaBoSS relative time; observation stops at the horizon and later switches are censored",
                "workers": req.workers,
            },
            "event_definition": EVENT_DEFINITION,
            "positions": {
                "figure_position": req.position,
                "definitions": S.POSITION_DEFINITIONS,
            },
            "figure": {
                "direction_row_min_fraction": S.DIRECTION_ROW_MIN_FRACTION,
                "unresolved_adjacent_rule": "|P(upper row first) - 0.5| < 0.1 with >= 50 trajectories where both switch in an identifiable order",
            },
            "annotation_sources": annotation_sources(spec.model_version, active_root),
            "software": _versions(),
            "implementation_files": [
                describe_file(path, root=active_root).__dict__
                for path in implementation_files(active_root)
            ],
            "configuration_files": [
                describe_file(path, root=active_root).__dict__
                for path in configuration_files(active_root)
            ],
            "diagnostics": diagnostics,
            "runtime_s": round(time.time() - started, 1),
            "outputs": {},
        }
        for path in sorted(out.iterdir()):
            if path.name != "metadata.json":
                record = {
                    "path": str(final / path.name),
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
                if final.is_relative_to(active_root.resolve()):
                    record["path"] = str(
                        (final / path.name).relative_to(active_root.resolve())
                    )
                meta["outputs"][path.name] = record
        (out / "metadata.json").write_text(
            json.dumps(meta, indent=2, default=_json_default) + "\n", encoding="utf-8"
        )
    except BaseException:
        shutil.rmtree(out, ignore_errors=True)
        raise
    try:
        commit_staging(out, final, overwrite=req.overwrite)
    except BaseException:
        # Only a staging directory that was never swapped in is removed; once
        # renamed, its contents are the bundle at ``final``.
        if out.exists():
            shutil.rmtree(out, ignore_errors=True)
        raise
    return final


_RUN_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
BUNDLE_FILES = (
    "events.tsv",
    "node_summary.tsv",
    "control_comparison.tsv",
    "pairwise_precedence.tsv",
    "cascade.png",
    "cascade.svg",
    "cascade.pdf",
    "metadata.json",
)


def bundle_directory(out_root: Path, run_id: str, *, overwrite: bool = False) -> Path:
    """The bundle directory for ``run_id``, refused unless it is safe to write.

    ``run_id`` must be a plain name (no separator, no ``..``), the directory must
    resolve inside ``out_root``, and an existing non-empty directory is refused
    unless ``overwrite`` is set and it holds nothing but bundle files: a bundle is
    never mixed with, or written over, anything else.
    """
    if not _RUN_ID_RE.fullmatch(run_id) or ".." in run_id:
        raise ValueError(
            f"run id must be a plain name ({_RUN_ID_RE.pattern}), got {run_id!r}"
        )
    root = out_root.resolve()
    out = (root / run_id).resolve()
    if out.parent != root:
        raise ValueError(f"run id {run_id!r} resolves outside {root}")
    _refuse_unless_replaceable(out, overwrite=overwrite)
    return out


def _refuse_unless_replaceable(out: Path, *, overwrite: bool) -> None:
    """Raise unless ``out`` is absent, empty, or (with ``overwrite``) a bundle only."""
    if out.is_symlink():
        # Checked first: a link swapped in after the preflight would make the
        # replacement act on whatever it points to, possibly outside the root.
        raise FileExistsError(f"{out} is a symbolic link, not a bundle directory")
    if not out.exists():
        return
    if not out.is_dir():
        raise ValueError(f"{out} exists and is not a directory")
    present = {p.name for p in out.iterdir()}
    if present and not overwrite:
        raise FileExistsError(
            f"{out} already holds a bundle; choose another run id or pass overwrite"
        )
    foreign = sorted(present - set(BUNDLE_FILES))
    irregular = sorted(
        p.name for p in out.iterdir() if p.is_symlink() or not p.is_file()
    )
    if irregular:
        raise FileExistsError(
            f"{out} holds entries that are not regular files: {irregular}; "
            "an overwrite replaces bundle files only"
        )
    if foreign:
        raise FileExistsError(f"{out} holds files that are not a bundle's: {foreign}")


def begin_staging(final: Path) -> Path:
    """A fresh staging directory beside ``final``.

    Its name starts with a dot, which a run id cannot, so it never collides with
    a bundle.
    """
    final.parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f".{final.name}.staging-", dir=final.parent))


#: Replaced bundles are moved here, inside the output root, and never deleted.
TRASH = ".trash"


def commit_staging(staging: Path, final: Path, *, overwrite: bool = False) -> None:
    """Replace ``final`` with the complete ``staging`` directory; delete nothing.

    The preflight in ``bundle_directory`` ran before the simulation, so the
    target may have changed since: another run may have committed a bundle
    there, or something else may have written into it. The commit therefore
    holds an exclusive lock on the parent directory (cascade runs commit one at
    a time) and checks the target again under it, refusing an existing bundle
    without ``overwrite`` and any entry that is not a bundle file.

    A replaced bundle is not removed: it is moved, whole, into ``TRASH`` beside
    the bundles (``<out_root>/.trash/<run id>.<unique>``). So nothing written
    into it at any moment, a late file under a bundle file's name included, is
    ever deleted; emptying the trash is left to the user. Moved aside, it is
    checked once more, and restored if anything foreign reached it or the swap
    fails. The contract this relies on: one writer per bundle directory, the
    cascade itself; anything else writing there is preserved, not coordinated.
    """
    lock = os.open(final.parent, os.O_RDONLY)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        _refuse_unless_replaceable(final, overwrite=overwrite)
        old = None
        if final.exists():
            trash = final.parent / TRASH
            if trash.is_symlink() or (trash.exists() and not trash.is_dir()):
                # A link would move the replaced bundle wherever it points.
                raise FileExistsError(
                    f"{trash} is not a plain directory; the replaced bundle "
                    "must stay inside the output root"
                )
            trash.mkdir(exist_ok=True)
            old = Path(tempfile.mkdtemp(prefix=f"{final.name}.", dir=trash))
            old.rmdir()
            final.rename(old)
            try:
                _refuse_unless_replaceable(old, overwrite=True)
            except BaseException:
                old.rename(final)
                raise
        try:
            staging.rename(final)
        except BaseException:
            if old is not None:
                old.rename(final)
            raise
    finally:
        os.close(lock)  # releases the lock


def implementation_files(root: Path) -> list[Path]:
    """Every code and configuration file a bundle's numbers depend on, hashed so
    that a run on a dirty tree (``source_commit`` ending ``-dirty``) or outside
    git still names its inputs.

    The cascade package and the spec parser, plus the repository's simulation
    inventory (``concordance.simulate.IMPLEMENTATION_GLOBS``: the runner, the
    MaBoSS adapter, the model, protocol and calibration code, the intervention
    engine and its library). The model files, the protocol file and every
    lineage phase's condition cfg are recorded separately, under ``model`` and
    ``starting_state``. Every ``dt_adoc`` module the run imported is added too.
    """
    cascade = sorted((root / "src/dt_adoc/cascade").glob("*.py"))
    shared = [root / relative for relative in simulation_implementation_files(root)]
    return sorted(
        {
            *cascade,
            root / "src/dt_adoc/perturbations/spec.py",
            *shared,
            *loaded_package_files(root),
        }
    )


#: Every file under these directories is recorded by content: protocol and
#: calibration settings, the intervention library and its governance tables, the
#: model registry (each version's provenance.toml) and every model version's
#: network, cfgs and condition cfgs, including parents a version is resolved
#: against.
CONFIGURATION_DIRECTORIES = ("config", "models")


def configuration_files(root: Path) -> list[Path]:
    """Every file under ``CONFIGURATION_DIRECTORIES``, tracked or not."""
    return sorted(
        path
        for directory in CONFIGURATION_DIRECTORIES
        for path in (root / directory).rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )


def loaded_package_files(root: Path) -> list[Path]:
    """Every ``dt_adoc`` module file this process has imported from ``root``.

    The static list above names what the numbers are known to depend on; this
    adds whatever the run actually imported, so a dependency added later is
    recorded without anyone remembering to list it.
    """
    package = (root / "src" / "dt_adoc").resolve()
    files = set()
    for name, module in list(sys.modules.items()):
        path = getattr(module, "__file__", None)
        if name.split(".")[0] == "dt_adoc" and path:
            resolved = Path(path).resolve()
            if resolved.is_relative_to(package):
                files.add(root / resolved.relative_to(root.resolve()))
    return sorted(files)


def run_diagnostics(perturbed, control) -> dict[str, Any]:
    """Run-level checks a reader needs before interpreting the cascade."""

    def arm(ev):
        switched = ev.n_switches_min > 0
        disagrees = ev.rule_disagrees_at_horizon.map(lambda v: v is True or v == "True")
        agrees = ev.rule_disagrees_at_horizon.map(lambda v: v is False or v == "False")
        unknown = ~(disagrees | agrees)
        per_traj = switched.groupby(ev.trajectory).any()
        return {
            "fraction_trajectories_with_any_switch": float(per_traj.mean()),
            "node_trajectory_cells_switching": int(switched.sum()),
            "cells_n_switches_min_gt_1": int((ev.n_switches_min > 1).sum()),
            "cells_first_switch_unresolved": int(
                (ev.first_switch_resolved == False).sum()
            ),
            "cells_final_unknown": int(ev.final.isna().sum()),
            "cells_rule_disagrees_at_horizon": int(disagrees.sum()),
            "cells_rule_unknown_at_horizon": int(unknown.sum()),
            "cells_no_switch_rule_disagrees_at_horizon": int(
                (~switched & disagrees).sum()
            ),
            "fraction_trajectories_at_fixed_point_at_horizon": float(
                agrees.groupby(ev.trajectory).all().mean()
            ),
        }

    c = arm(control)
    stationary = (
        c["node_trajectory_cells_switching"] == 0
        and c["cells_rule_disagrees_at_horizon"] == 0
        and c["cells_rule_unknown_at_horizon"] == 0
        and c["cells_final_unknown"] == 0
    )
    return {
        "perturbed": arm(perturbed),
        "control": c,
        "control_stationary": stationary,
        "note": "control_stationary requires, in every control trajectory, that no "
        "node switched and that every node's rule is known and agrees with its "
        "value at the horizon: the start is then a fixed point of the control's "
        "rules, so every perturbed-arm switch is perturbation-associated under the "
        "model. Anything less (a switch, a disagreeing rule, an unevaluable one) "
        "makes it false",
    }


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, Path):
        return str(value)
    return str(value)
