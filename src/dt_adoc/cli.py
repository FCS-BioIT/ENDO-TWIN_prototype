"""Command-line interface for DT_ADOC."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dt_adoc import __version__
from dt_adoc.calibration.adhesion_likelihood import binomial_log_likelihood
from dt_adoc.maboss_adapter import runtime_report
from dt_adoc.model.runtime import available_models
from dt_adoc.model.validate import validate as validate_model_contract
from dt_adoc.perturbations.target_engagement import build_target_engagement_grid


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dt-adoc")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    runtime = subparsers.add_parser("runtime-report")
    runtime.add_argument("--json", action="store_true")

    grid = subparsers.add_parser("target-grid")
    grid.add_argument("--levels", nargs="+", type=float, required=True)

    adhesion = subparsers.add_parser("adhesion-ll")
    adhesion.add_argument("--probability", type=float, required=True)
    adhesion.add_argument("--successes", type=int, required=True)
    adhesion.add_argument("--trials", type=int, required=True)

    path_check = subparsers.add_parser("path-report")
    path_check.add_argument("path", type=Path)

    validate_models = subparsers.add_parser("validate-models")
    validate_models.add_argument("--json", action="store_true")
    validate_models.add_argument(
        "--model-version",
        choices=sorted(available_models()),
        default=None,
    )

    smoke = subparsers.add_parser("smoke")
    smoke.add_argument("--run-id", default="phase1-structural-smoke")
    smoke.add_argument(
        "--model-version",
        choices=sorted(available_models()),
        default="adoc-core-v0.1.0",
    )

    protein_table = subparsers.add_parser(
        "build-protein-table",
        help="Build the canonical ADOC secreted-protein input table and its "
        "validation report from the source workbook",
    )
    protein_table.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Override the source workbook path (defaults to "
        "data/proteinas secretadas ADOC.xlsx).",
    )
    protein_table.add_argument("--output", type=Path, default=None)
    protein_table.add_argument("--validation-report", type=Path, default=None)
    protein_table.add_argument("--json", action="store_true")

    citations = subparsers.add_parser(
        "verify-citations",
        help="Resolve every bibliography DOI and refresh the verification cache",
    )
    citations.add_argument("--checked-on", default="")
    citations.add_argument(
        "--offline",
        action="store_true",
        help="Only run the offline structural and cache checks.",
    )

    constraints = subparsers.add_parser(
        "evaluate-constraints",
        help="Evaluate the directional observation-to-model constraints",
    )
    constraints.add_argument(
        "--model",
        dest="model_version",
        choices=sorted(available_models()),
        default="adoc-literature-superset-v0.3.0",
    )
    constraints.add_argument("--seed", type=int, default=1)
    constraints.add_argument("--trajectories", type=int, default=2000)
    constraints.add_argument("--converged-duration", type=float, default=30.0)
    constraints.add_argument("--json", action="store_true")

    structure = subparsers.add_parser(
        "render-structure",
        help="Render the static structural topology figure for a model",
    )
    structure.add_argument("--model", default="adoc-literature-superset-v0.3.0")
    structure.add_argument("--output", default=None)
    structure.add_argument("--json", action="store_true")

    identifiability = subparsers.add_parser(
        "render-identifiability",
        help=("Render the experimental-identifiability figure and tables for a model"),
    )
    identifiability.add_argument("--model", default="adoc-literature-superset-v0.4.0")
    identifiability.add_argument("--output", default=None)
    identifiability.add_argument("--json", action="store_true")

    design_alias = subparsers.add_parser(
        "render-design-alias",
        help=(
            "Render the design-equivalence figures and tables for the planned "
            "experimental arms in config/planned_design.yaml"
        ),
    )
    design_alias.add_argument("--output", default=None)
    design_alias.add_argument(
        "--variant",
        default=None,
        help="a sensitivity_variants key from config/planned_design.yaml",
    )
    design_alias.add_argument("--json", action="store_true")

    dynamics = subparsers.add_parser(
        "render-dynamics",
        help="Render the sequential MaBoSS pathway-dynamics animation",
    )
    dynamics.add_argument(
        "--model",
        dest="model_version",
        choices=sorted(available_models()),
        default="adoc-literature-v0.2.0",
    )
    dynamics.add_argument(
        "--protocol-suite",
        default="reference-sequence",
        choices=["reference-sequence"],
        help="Protocol lineage to animate; the reference sequence is the "
        "model's declared continuation chain.",
    )
    dynamics.add_argument(
        "--terminal-protocol",
        default="adhesion_challenge_washout",
        help="Protocol the lineage terminates at.",
    )
    dynamics.add_argument("--seed", type=int, default=1)
    dynamics.add_argument("--trajectories", type=int, default=2000)
    dynamics.add_argument(
        "--phase-horizon",
        type=float,
        default=None,
        help=(
            "Override every phase's declared duration for the simulation, so the "
            "network is read at its logical fixed point. Dimensionless MaBoSS "
            "relative time, never a day count. Omit to use the committed "
            "durations in config/protocols.yaml."
        ),
    )
    dynamics.add_argument("--frame-stride", type=int, default=2)
    dynamics.add_argument("--frame-duration", type=int, default=260)
    dynamics.add_argument("--readme-max-width", type=int, default=1100)
    dynamics.add_argument("--figure-width", type=float, default=16.0)
    dynamics.add_argument("--figure-height", type=float, default=9.0)
    dynamics.add_argument("--dpi", type=int, default=76)
    dynamics.add_argument("--node-fontsize", type=float, default=6.6)
    dynamics.add_argument("--font-scale", type=float, default=1.0)
    dynamics.add_argument("--run-id", default="readme-demo")
    dynamics.add_argument("--view", choices=["overview", "full"], default="overview")
    dynamics.add_argument(
        "--output",
        type=Path,
        default=Path("docs/assets/adoc_maboss_pathway_dynamics.gif"),
    )
    dynamics.add_argument("--preview", type=Path, default=None)
    dynamics.add_argument("--metadata", type=Path, default=None)
    dynamics.add_argument(
        "--no-full-resolution",
        action="store_true",
        help="Skip the full-resolution run-output animation.",
    )
    dynamics.add_argument(
        "--trajectory-dir",
        type=Path,
        default=None,
        help=(
            "Repo-relative directory for the per-phase trajectory tables and "
            "executed cfgs (default: the gitignored run directory)."
        ),
    )
    perturb = subparsers.add_parser(
        "perturb",
        help="Perturbation-response analyses from an established protocol state",
    )
    perturb_sub = perturb.add_subparsers(dest="perturb_command", required=True)
    cascade = perturb_sub.add_parser(
        "cascade",
        help="Per-trajectory response order after a declared perturbation, "
        "with a matched unperturbed control",
    )
    cascade.add_argument("--spec", type=Path, default=None, help="perturbations/*.yaml")
    cascade.add_argument(
        "--model",
        dest="model_version",
        default=None,
        help="model version (default: dt_adoc.cascade.cli.DEFAULT_MODEL_VERSION)",
    )
    cascade.add_argument(
        "--start", default=None, help="protocol whose end state is perturbed"
    )
    cascade.add_argument(
        "--set",
        dest="set_inputs",
        action="append",
        default=[],
        metavar="IN_NODE=0|1",
        help="change a declared model input at the perturbation boundary",
    )
    cascade.add_argument(
        "--intervention",
        dest="interventions",
        action="append",
        default=[],
        help="a registered intervention-library id (repeatable)",
    )
    cascade.add_argument(
        "--rule-variant",
        dest="rule_variants",
        action="append",
        default=[],
        metavar="FAMILY=VARIANT",
    )
    cascade.add_argument("--name", default=None)
    cascade.add_argument("--description", default="")
    cascade.add_argument("--n", dest="n_trajectories", type=int, default=2000)
    cascade.add_argument("--seed", dest="master_seed", type=int, default=20261008)
    cascade.add_argument(
        "--horizon",
        type=float,
        default=25.0,
        help="perturbed-phase horizon (MaBoSS relative time)",
    )
    cascade.add_argument("--tick", type=float, default=0.01)
    cascade.add_argument(
        "--init-horizon",
        type=float,
        default=25.0,
        help="lineage phase horizon; 0 = declared durations",
    )
    cascade.add_argument("--memory-policy", default="all_non_inputs")
    cascade.add_argument(
        "--position",
        default=None,
        choices=["normalized_time", "normalized_rank", "absolute_time"],
    )
    cascade.add_argument("--workers", type=int, default=4)
    cascade.add_argument("--run-id", default=None)
    cascade.add_argument(
        "--overwrite",
        action="store_true",
        help="replace an existing bundle with the same run id",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "runtime-report":
        payload = runtime_report()
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            for key, value in payload.items():
                print(f"{key}: {value}")
        return 0
    if args.command == "target-grid":
        print(json.dumps(build_target_engagement_grid(args.levels), indent=2))
        return 0
    if args.command == "adhesion-ll":
        value = binomial_log_likelihood(
            probability=args.probability,
            successes=args.successes,
            trials=args.trials,
        )
        print(f"{value:.10f}")
        return 0
    if args.command == "path-report":
        print(args.path.resolve())
        return 0
    if args.command == "validate-models":
        payload = validate_model_contract(model_version=args.model_version).payload()
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(json.dumps(payload, sort_keys=True))
        return 0 if payload["status"] == "valid" else 1
    if args.command == "smoke":
        from dt_adoc.simulation.runner import run_structural_smoke

        output_root = run_structural_smoke(
            run_id=args.run_id,
            model_version=args.model_version,
        )
        print(output_root)
        return 0
    if args.command == "build-protein-table":
        # Deferred like `smoke`/`render-dynamics`: openpyxl is only needed for
        # this subcommand, so the rest of the CLI stays importable without it.
        from dt_adoc.data.secreted_proteins import build_and_validate

        result = build_and_validate(
            source_path=args.source,
            table_path=args.output,
            validation_path=args.validation_report,
        )
        payload = {
            "row_count": result["row_count"],
            "table_path": str(result["table_path"]),
            "validation_path": str(result["validation_path"]),
            "status": result["status"],
            "errors": result["errors"],
            "warnings": result["warnings"],
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(
                f"rows={payload['row_count']} status={payload['status']} "
                f"warnings={len(payload['warnings'])}"
            )
            print(f"table: {payload['table_path']}")
            print(f"validation report: {payload['validation_path']}")
            for err in payload["errors"]:
                print(f"ERROR: {err}")
            for warn in payload["warnings"]:
                print(f"WARNING: {warn}")
        return 0 if result["status"] == "structurally_valid" else 1
    if args.command == "verify-citations":
        from dt_adoc.evidence.citations import (
            check_bibliography,
            check_resolution_cache,
            verify_and_write_cache,
        )

        if not args.offline:
            rows = verify_and_write_cache(checked_on=args.checked_on)
            resolved = sum(1 for r in rows if r["resolved"] == "true")
            print(f"resolved {resolved}/{len(rows)} references")
        structural = check_bibliography()
        cached = check_resolution_cache()
        payload = {
            "bibliography": structural.payload(),
            "resolution": cached.payload(),
        }
        print(json.dumps(payload, indent=2))
        return 0 if not (structural.errors or cached.errors) else 1
    if args.command == "evaluate-constraints":
        # Deferred: needs the MaBoSS runtime. This reports the directional
        # checks and never touches the fitted adhesion likelihood.
        from dt_adoc.calibration.observation_map import (
            evaluate_directional_constraints,
            load_observation_map,
            simulate_constraint_protocols,
        )

        rows = load_observation_map()
        simulated = simulate_constraint_protocols(
            model_version=args.model_version,
            seed=args.seed,
            trajectory_count=args.trajectories,
            converged_duration=args.converged_duration,
        )
        checks = evaluate_directional_constraints(simulated, rows)
        excluded = any(check.excludes_candidate for check in checks)
        # C2: each check carries its measurement's compartment attribution
        # (OM-002: CA-002, epithelial/stromal ambiguous). The numbers are the
        # evaluator's, unchanged.
        from dt_adoc.observations.compartment_attribution import (
            annotated_checks_payload,
            describe_check,
        )

        annotated = annotated_checks_payload(checks)
        payload = {
            "model_version": args.model_version,
            "converged_duration": args.converged_duration,
            "candidate_excluded": excluded,
            **annotated,
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            for c in annotated["checks"]:
                print(
                    f"{c['value_high']:.4f} vs {c['value_low']:.4f}  {describe_check(c)}"
                )
            print(f"candidate_excluded={excluded}")
        return 0
    if args.command == "render-identifiability":
        # Eager-safe: structural only. It reads network.bnd, the condition cfgs
        # and the observation tables, and runs no simulation.
        from dt_adoc.reporting.identifiability_figure import (
            render_identifiability_artifact,
        )

        metadata = render_identifiability_artifact(
            args.model,
            Path(args.output) if args.output else None,
        )
        if args.json:
            print(json.dumps(metadata, indent=2))
        else:
            for figure in metadata["figures"]:
                print(f"figure   {figure['path']}  {figure['sha256'][:12]}")
            for table in metadata["tables"]:
                print(f"table    {table['path']}  ({table['rows']} rows)")
            print(f"metadata {metadata['metadata_path']}")
            for key, value in metadata["ceilings"].items():
                print(f"  {key:44s} {value}")
        return 0
    if args.command == "render-structure":
        # Eager-safe: the structural figure needs no MaBoSS runtime, only
        # network.bnd and two config tables.
        from dt_adoc.reporting.structure_figure import render_structure_artifact

        metadata = render_structure_artifact(
            args.model,
            Path(args.output) if args.output else None,
        )
        if args.json:
            print(json.dumps(metadata, indent=2))
        else:
            print(f"figure   {metadata['figure']['path']}")
            print(f"sha256   {metadata['figure']['sha256']}")
            print(f"metadata {metadata['metadata_path']}")
        return 0

    if args.command == "render-design-alias":
        # Eager-safe: structural only. It reads network.bnd, the condition cfgs
        # and config/planned_design.yaml, and runs no simulation.
        from dt_adoc.reporting.design_alias_figure import (
            render_design_alias_artifact,
        )

        metadata = render_design_alias_artifact(
            Path(args.output) if args.output else None,
            variant=args.variant,
        )
        if args.json:
            print(json.dumps(metadata, indent=2))
        else:
            for figure in metadata["figures"]:
                print(f"figure   {figure['path']}  {figure['sha256'][:12]}")
            for table in metadata["tables"]:
                print(f"table    {table['path']}  ({table['rows']} rows)")
            print(f"metadata {metadata['metadata_path']}")
            summary = metadata["summary"]
            print(
                f"design states {summary['design_effective_states']} of "
                f"{summary['global_effective_states']} Boolean functions; "
                f"largest indistinguishable class {summary['largest_design_class']}"
            )
        return 0

    if args.command == "perturb" and args.perturb_command == "cascade":
        # Deferred: the cascade needs the MaBoSS runtime.
        from dt_adoc.cascade.cli import run_from_args

        return run_from_args(args)

    if args.command == "render-dynamics":
        # Deferred like `smoke`: rendering needs the MaBoSS runtime, and the
        # other subcommands must stay importable without it.
        from dt_adoc.reporting.render_dynamics import (
            RenderRequest,
            render_pathway_dynamics,
        )

        metadata = render_pathway_dynamics(
            RenderRequest(
                model_version=args.model_version,
                terminal_protocol=args.terminal_protocol,
                view=args.view,
                seed=args.seed,
                trajectory_count=args.trajectories,
                phase_horizon=args.phase_horizon,
                frame_stride=args.frame_stride,
                frame_duration_ms=args.frame_duration,
                readme_max_width=args.readme_max_width,
                figure_width=args.figure_width,
                figure_height=args.figure_height,
                dpi=args.dpi,
                node_fontsize=args.node_fontsize,
                font_scale=args.font_scale,
                run_id=args.run_id,
                output=args.output,
                preview=args.preview,
                metadata=args.metadata,
                write_full_resolution=not args.no_full_resolution,
                trajectory_dir=args.trajectory_dir,
            )
        )
        print(json.dumps(metadata["paths"], indent=2))
        print(
            f"frames={metadata['readme_animation']['frame_count']} "
            f"bytes={metadata['readme_animation']['gif_bytes']} "
            f"nodes={metadata['visualization']['node_count']} "
            f"edges={metadata['visualization']['edge_count']}"
        )
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
