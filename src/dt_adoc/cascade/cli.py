"""``dt_adoc.cli perturb cascade``: turn arguments into a ``CascadeRequest``."""

from __future__ import annotations

import argparse
import json

from dt_adoc.cascade.run import DEFAULT_POSITION, CascadeRequest, run_cascade
from dt_adoc.cascade.simulate import PhaseSettings, StartSettings
from dt_adoc.perturbations.spec import PerturbationSpecError, load_spec, parse_spec

#: The cascade runs interventions through the engine, so the current markerless
#: increment is the right default here. It is kept out of ``dt_adoc/cli.py`` on
#: purpose: the cfg-reading static analyses there must default to a marker-timed
#: version (``tests/unit/test_v060_marker_removal.StaticAnalysisPinTest``).
DEFAULT_MODEL_VERSION = "adoc-literature-superset-v0.6.0"


def _pairs(values: list[str], what: str) -> dict[str, str]:
    out = {}
    for item in values:
        key, sep, value = item.partition("=")
        if not sep or not key or not value:
            raise PerturbationSpecError(f"{what} expects KEY=VALUE, got {item!r}")
        if key in out:
            raise PerturbationSpecError(f"{what} names {key} twice")
        out[key] = value
    return out


def spec_from_args(args: argparse.Namespace):
    inline = bool(args.set_inputs or args.interventions or args.rule_variants)
    if args.spec is not None:
        if inline or args.start or args.model_version:
            raise PerturbationSpecError(
                "--spec cannot be combined with --model/--start/--set/--intervention/--rule-variant"
            )
        return load_spec(args.spec)
    if not args.start:
        raise PerturbationSpecError("give --spec, or --start with at least one effect")
    inputs = {}
    for key, value in _pairs(args.set_inputs, "--set").items():
        if value not in ("0", "1"):
            raise PerturbationSpecError(f"--set {key} takes 0 or 1, got {value!r}")
        inputs[key] = value == "1"
    parts = [f"{k.lower()}_{'on' if v else 'off'}" for k, v in sorted(inputs.items())]
    parts += list(args.interventions)
    name = args.name or "__".join([args.start, *parts])[:64].lower()
    return parse_spec(
        {
            "name": name,
            "description": args.description,
            "model_version": args.model_version or DEFAULT_MODEL_VERSION,
            "start": args.start,
            "input_changes": inputs,
            "interventions": list(args.interventions),
            "rule_variants": _pairs(args.rule_variants, "--rule-variant"),
        },
        source="command line",
    )


def run_from_args(args: argparse.Namespace) -> int:
    spec = spec_from_args(args)
    request = CascadeRequest(
        spec=spec,
        n_trajectories=args.n_trajectories,
        master_seed=args.master_seed,
        start=StartSettings(
            init_horizon=None if args.init_horizon == 0 else args.init_horizon,
            memory_policy=args.memory_policy,
        ),
        phase=PhaseSettings(horizon=args.horizon, tick=args.tick),
        position=args.position or DEFAULT_POSITION,
        workers=args.workers,
        run_id=args.run_id,
        overwrite=args.overwrite,
    )
    out = run_cascade(request)
    print(json.dumps({"bundle": str(out)}, indent=2))
    return 0
