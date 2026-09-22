"""Orchestrate the MaBoSS pathway-dynamics animation and its artifacts.

Running this executes exactly the protocol lineage the animation shows -- five
or six bounded MaBoSS runs. It never triggers a calibration fit, a perturbation
screen or the full structural smoke.

Artifacts are deliberately timestamp-free so that re-running with the same
model, protocol lineage, seed and trajectory count reproduces byte-identical
metadata alongside the committed GIF.
"""

from __future__ import annotations

import json
import platform
import re
from dataclasses import asdict, dataclass
from importlib import metadata as package_metadata
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from dt_adoc.model.provenance import describe_file, source_commit
from dt_adoc.model.runtime import resolve_model
from dt_adoc.protocols.conditions import protocol_file
from dt_adoc.reporting.dynamics import (
    VIEW_OVERVIEW,
    build_network_view,
    load_visualization_config,
)
from dt_adoc.reporting.network_figure import RenderSettings, render_animation
from dt_adoc.simulation.timeline import (
    DEFAULT_TERMINAL_PROTOCOL,
    build_sequential_timeline,
)

DEFAULT_README_GIF = Path("docs/assets/adoc_maboss_pathway_dynamics.gif")
DEFAULT_PREVIEW_PNG = Path("docs/assets/adoc_maboss_pathway_dynamics_preview.png")
DEFAULT_METADATA = Path("docs/assets/adoc_maboss_pathway_dynamics_metadata.json")
FULL_GIF_NAME = "adoc_maboss_pathway_dynamics_full.gif"

#: Suffixes that derive the preview and metadata paths from the requested GIF.
#: Chosen so the committed artifact set derives itself exactly:
#: ``adoc_maboss_pathway_dynamics.gif`` -> ``..._preview.png`` / ``..._metadata.json``.
PREVIEW_SUFFIX = "_preview.png"
METADATA_SUFFIX = "_metadata.json"

#: The committed README artifact set, and the one model version that owns it.
#: README.md and scripts/make_chatgpt_results_bundle.sh reference these three
#: paths by name, so a render of any other model landing on one of them would
#: republish that model's numbers under this model's name.
#:
#: Declared here rather than read from a provenance.toml because every model in
#: models/ declares an immutability flag -- `immutable` for the baseline,
#: `immutable_parent` for both others -- so that flag cannot say which model
#: owns these files.
README_ARTIFACT_OWNER = "adoc-literature-v0.2.0"
README_ARTIFACTS = frozenset(
    {DEFAULT_README_GIF, DEFAULT_PREVIEW_PNG, DEFAULT_METADATA}
)


@dataclass(frozen=True)
class RenderRequest:
    """Everything that determines the rendered output."""

    model_version: str = "adoc-literature-v0.2.0"
    terminal_protocol: str = DEFAULT_TERMINAL_PROTOCOL
    view: str = VIEW_OVERVIEW
    seed: int = 1
    trajectory_count: int = 2000
    frame_stride: int = 2
    figure_width: float = 16.0
    figure_height: float = 9.0
    dpi: int = 76
    node_fontsize: float = 6.6
    font_scale: float = 1.0
    frame_duration_ms: int = 260
    readme_max_width: int = 1100
    run_id: str = "readme-demo"
    #: Overrides every phase's declared duration for the SIMULATION only, so the
    #: network can be read at its logical fixed point. None keeps the committed
    #: durations. Dimensionless MaBoSS relative time, never a day count.
    phase_horizon: float | None = None
    output: Path = DEFAULT_README_GIF
    preview: Path | None = None
    metadata: Path | None = None
    write_full_resolution: bool = True
    #: Repo-relative directory for the per-phase trajectory tables and executed
    #: cfgs. None keeps them in the gitignored run directory; set it when the
    #: artifact is committed, so every declared source resolves in the repo.
    trajectory_dir: Path | None = None


@dataclass(frozen=True)
class OutputPaths:
    """The repo-relative paths one render is authorised to write."""

    gif: Path
    preview: Path
    metadata: Path
    trajectories: Path | None = None


def _sibling(output: Path, suffix: str) -> Path:
    return output.with_name(output.stem + suffix)


def _repo_relative(path: Path, *, label: str, root: Path) -> Path:
    candidate = path if path.is_absolute() else root / path
    try:
        return candidate.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(
            f"{label}={path} resolves outside the repository root {root}. "
            "Every render artifact must be repo-relative so its provenance can "
            "be recorded."
        ) from exc


def resolve_output_paths(request: RenderRequest, *, root: Path) -> OutputPaths:
    """Resolve, derive and authorise every path this render will write.

    Called before any simulation starts, so a bad destination costs nothing.
    Two defects are closed here.

    ``preview`` and ``metadata`` used to fall back to the frozen ``docs/assets``
    defaults *independently of* ``output``, so rendering a different model with
    only ``--output`` set wrote its GIF to the new path while overwriting the
    committed preview PNG and metadata JSON of ``adoc-literature-v0.2.0``. They
    are now derived from ``output``'s stem. That derivation reproduces the
    committed names exactly, so the ``render-dynamics-demo`` task and the
    documented single-argument command are unaffected, and it can never cross
    model versions.

    A destination outside ``root`` used to fail only at the very end, inside
    ``relative_to``, after the whole animation had already been rendered.

    The one remaining way to aim at a committed artifact is to name it
    explicitly, which is refused for any model that does not own it.
    """
    output = Path(request.output)
    candidates = {
        "output": output,
        "preview": (
            Path(request.preview)
            if request.preview
            else _sibling(output, PREVIEW_SUFFIX)
        ),
        "metadata": (
            Path(request.metadata)
            if request.metadata
            else _sibling(output, METADATA_SUFFIX)
        ),
    }
    relative: dict[str, Path] = {}
    for label, path in candidates.items():
        resolved = _repo_relative(path, label=label, root=root)
        if (
            resolved in README_ARTIFACTS
            and request.model_version != README_ARTIFACT_OWNER
        ):
            raise ValueError(
                f"refusing to write {label}={resolved} while rendering "
                f"{request.model_version}: that file is the committed "
                f"{README_ARTIFACT_OWNER} artifact referenced by README.md. "
                "Give --output a path of its own; --preview and --metadata are "
                "derived from it."
            )
        relative[label] = resolved
    trajectories = (
        _repo_relative(Path(request.trajectory_dir), label="trajectory_dir", root=root)
        if request.trajectory_dir
        else None
    )
    return OutputPaths(
        gif=relative["output"],
        preview=relative["preview"],
        metadata=relative["metadata"],
        trajectories=trajectories,
    )


def _cfg_setting(text: str, key: str) -> float | None:
    """The last ``key = value;`` in a merged cfg, which is the one MaBoSS uses."""
    values = re.findall(rf"^\s*{key}\s*=\s*([^;]+);", text, re.MULTILINE)
    return float(values[-1]) if values else None


def _package_version(name: str) -> str:
    try:
        return package_metadata.version(name)
    except package_metadata.PackageNotFoundError:
        return "unavailable"


def _runtime_versions() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "maboss": _package_version("maboss"),
        "matplotlib": _package_version("matplotlib"),
        "pandas": _package_version("pandas"),
        "numpy": _package_version("numpy"),
        "pillow": _package_version("pillow"),
    }


def _run_directory(model_spec: Any, run_id: str, root: Path) -> Path:
    return root / "output" / "visualization" / model_spec.model_version / run_id


def render_pathway_dynamics(
    request: RenderRequest,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Build the timeline, render the animation, and record provenance."""
    active_root = root or Path(__file__).resolve().parents[3]
    paths = resolve_output_paths(request, root=active_root)
    # Taken before anything is written: the render's own outputs land in
    # tracked paths and would otherwise mark every committed render dirty.
    commit = source_commit(active_root)
    model_spec = resolve_model(request.model_version, active_root)
    config = load_visualization_config(active_root)

    timeline = build_sequential_timeline(
        model_version=request.model_version,
        terminal_protocol=request.terminal_protocol,
        root=active_root,
        seed=request.seed,
        trajectory_count=request.trajectory_count,
        phase_horizon=request.phase_horizon,
    )
    view = build_network_view(
        model_version=request.model_version,
        view=request.view,
        root=active_root,
        config=config,
        model_spec=model_spec,
    )

    run_dir = _run_directory(model_spec, request.run_id, active_root)
    run_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = (
        active_root / paths.trajectories if paths.trajectories else run_dir / "raw"
    )
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Persist the exact trajectory the animation was drawn from, one compact
    # table per phase, so any displayed value can be checked against source,
    # and the merged cfg MaBoSS executed, so the run can be reconstructed.
    trajectory_refs: list[dict[str, Any]] = []
    executions: dict[int, dict[str, Any]] = {}
    for phase in timeline.phases:
        stem = f"{phase.protocol_id}__{phase.step_id}"
        rows = timeline.frame[timeline.frame["phase_index"] == phase.phase_index]
        path = raw_dir / f"{stem}_nodes_probtraj.tsv"
        rows.to_csv(path, sep="\t", index=False)
        trajectory_refs.append(
            {
                **describe_file(path, root=active_root).__dict__,
                "kind": "raw_nodes_probtraj",
                "protocol_id": phase.protocol_id,
                "step_id": phase.step_id,
                "phase_index": phase.phase_index,
            }
        )
        cfg_path = raw_dir / f"{stem}_executed.cfg"
        cfg_path.write_text(phase.executed_cfg_text, encoding="utf-8")
        executions[phase.phase_index] = {
            "condition_cfg": describe_file(
                active_root / phase.condition_cfg, root=active_root
            ).__dict__,
            "executed_cfg": describe_file(cfg_path, root=active_root).__dict__,
            "max_time": _cfg_setting(phase.executed_cfg_text, "max_time"),
            "time_tick": _cfg_setting(phase.executed_cfg_text, "time_tick"),
            "executed_network": phase.executed_network,
        }

    readme_path = active_root / paths.gif
    preview_path = active_root / paths.preview
    readme_stats = render_animation(
        view=view,
        timeline=timeline,
        output_path=readme_path,
        preview_path=preview_path,
        settings=RenderSettings(
            figsize=(request.figure_width, request.figure_height),
            dpi=request.dpi,
            node_fontsize=request.node_fontsize,
            font_scale=request.font_scale,
            frame_stride=request.frame_stride,
            frame_duration_ms=request.frame_duration_ms,
            max_width=request.readme_max_width,
            source_commit=commit,
        ),
    )

    full_stats: dict[str, Any] | None = None
    if request.write_full_resolution:
        full_stats = render_animation(
            view=view,
            timeline=timeline,
            output_path=run_dir / FULL_GIF_NAME,
            settings=RenderSettings(
                figsize=(request.figure_width, request.figure_height),
                dpi=request.dpi,
                node_fontsize=request.node_fontsize,
                font_scale=request.font_scale,
                frame_stride=request.frame_stride,
                frame_duration_ms=request.frame_duration_ms,
                max_width=None,
                source_commit=commit,
            ),
        )

    metadata = {
        "schema_version": "1.0",
        "artifact": paths.gif.stem,
        "source_commit": commit,
        "horizon_class": "declared" if request.phase_horizon is None else "converged",
        "phase_horizon": request.phase_horizon,
        "declared_phase_durations": {
            phase.label: phase.declared_duration for phase in timeline.phases
        },
        "claim_boundary": (
            "Visualises MaBoSS state probabilities through a sequential ADOC "
            "protocol. Not molecular concentrations, single-cell "
            "trajectories, spatial organisation, pathway flux, causal edge "
            "strength, PhysiBoSS output, clinical implantation probability, "
            "or validated drug efficacy. Every horizon is a dimensionless "
            "MaBoSS relative-time parameter, never a day or hour count; a "
            "converged-horizon render reads each phase at its logical fixed "
            "point, at which most nodes saturate to 0 or 1 and the remaining "
            "graded values are hand-set relay probabilities. See "
            "docs/endpoint_convergence_finding.md."
        ),
        "value_semantics": "P(node = ON) across simulated MaBoSS trajectories",
        "time_semantics": "MaBoSS relative time; no validated mapping to hours",
        "model": {
            "model_id": model_spec.model_id,
            "model_version": model_spec.model_version,
            "network_bnd": describe_file(
                model_spec.network_bnd, root=active_root
            ).__dict__,
            "node_dictionary": describe_file(
                model_spec.node_dictionary, root=active_root
            ).__dict__,
            "edge_evidence": describe_file(
                model_spec.edge_evidence, root=active_root
            ).__dict__,
            "phenotype_contract": describe_file(
                model_spec.phenotype_contract, root=active_root
            ).__dict__,
        },
        "protocol": {
            "terminal_protocol": request.terminal_protocol,
            "sequence": list(timeline.protocol_ids),
            "definition": describe_file(
                active_root / protocol_file(request.model_version, active_root),
                root=active_root,
            ).__dict__,
            "phases": [
                {
                    "phase_index": phase.phase_index,
                    "protocol_id": phase.protocol_id,
                    "step_id": phase.step_id,
                    "label": phase.label,
                    "phase_start": phase.phase_start,
                    "phase_end": phase.phase_end,
                    "continuation_from": phase.continuation_from,
                    "continuation_applied": phase.continuation_applied,
                    "input_states": phase.input_states,
                    # Only when declared, so a marker-timed figure's metadata
                    # keeps its exact shape. Interventions are not inputs.
                    **(
                        {"interventions": list(phase.interventions)}
                        if phase.interventions
                        else {}
                    ),
                    "execution": executions[phase.phase_index],
                }
                for phase in timeline.phases
            ],
        },
        "simulation": {
            "seed": timeline.seed,
            "trajectory_count": timeline.trajectory_count,
            "engine_backend": "cmaboss",
            "timeline_rows": len(timeline.frame),
            "runtime": _runtime_versions(),
        },
        "render_request": {
            key: (str(value) if isinstance(value, Path) else value)
            for key, value in asdict(request).items()
        },
        "visualization": {
            "view": request.view,
            "node_count": len(view.nodes),
            "edge_count": len(view.edges),
            "panels": [panel.key for panel in view.panels],
            "config": describe_file(
                active_root / "config" / "visualization.yaml", root=active_root
            ).__dict__,
        },
        "readme_animation": readme_stats,
        "full_resolution_animation": full_stats,
        "trajectory_sources": trajectory_refs,
    }

    metadata_path = active_root / paths.metadata
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    (run_dir / "animation_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )

    metadata["paths"] = {
        "readme_gif": str(paths.gif),
        "preview_png": str(paths.preview),
        "metadata_json": str(paths.metadata),
        "run_directory": str(run_dir.relative_to(active_root)),
    }
    return metadata
